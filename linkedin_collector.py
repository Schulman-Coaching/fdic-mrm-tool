"""
LinkedIn data collection for MRM leadership information
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from config import settings, MRM_KEYWORDS, LEADERSHIP_PATTERNS
from data_models import LeadershipInfo, DataSource
from database import db_manager

logger = logging.getLogger(__name__)

class LinkedInCollector:
    """Collects MRM leadership data from LinkedIn"""
    
    def __init__(self, username: str = None, password: str = None):
        self.username = username or settings.LINKEDIN_USERNAME
        self.password = password or settings.LINKEDIN_PASSWORD
        self.driver = None
        self.logged_in = False
        
        if not self.username or not self.password:
            logger.warning("LinkedIn credentials not provided. LinkedIn collection will be disabled.")
    
    def _setup_driver(self):
        """Setup Chrome driver with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument(f"user-agent={settings.USER_AGENT}")
        
        # Run in headless mode for automation
        chrome_options.add_argument("--headless")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logger.info("Chrome driver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Chrome driver: {e}")
            raise
    
    async def login(self) -> bool:
        """Login to LinkedIn"""
        if not self.username or not self.password:
            logger.error("LinkedIn credentials not provided")
            return False
        
        try:
            if not self.driver:
                self._setup_driver()
            
            logger.info("Attempting LinkedIn login...")
            self.driver.get("https://www.linkedin.com/login")
            
            # Wait for login form
            wait = WebDriverWait(self.driver, 10)
            
            # Enter username
            username_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
            username_field.clear()
            username_field.send_keys(self.username)
            
            # Enter password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(self.password)
            
            # Click login button
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Wait for successful login (check for feed or profile)
            try:
                wait.until(EC.any_of(
                    EC.presence_of_element_located((By.CLASS_NAME, "feed-identity-module")),
                    EC.presence_of_element_located((By.CLASS_NAME, "global-nav")),
                    EC.url_contains("/feed/")
                ))
                self.logged_in = True
                logger.info("Successfully logged into LinkedIn")
                return True
            except TimeoutException:
                logger.error("Login failed - could not detect successful login")
                return False
                
        except Exception as e:
            logger.error(f"LinkedIn login failed: {e}")
            return False
    
    def search_mrm_professionals(self, bank_name: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for MRM professionals at a specific bank"""
        if not self.logged_in:
            logger.error("Not logged into LinkedIn")
            return []
        
        try:
            # Construct search query
            mrm_keywords = ["model risk", "model validation", "quantitative risk", "risk management"]
            search_queries = []
            
            for keyword in mrm_keywords:
                query = f'"{keyword}" "{bank_name}"'
                search_queries.append(query)
            
            all_profiles = []
            
            for query in search_queries[:2]:  # Limit to 2 queries to avoid rate limiting
                profiles = self._search_linkedin_people(query, limit=10)
                all_profiles.extend(profiles)
                
                # Add delay between searches
                time.sleep(settings.SCRAPING_DELAY * 2)
            
            # Remove duplicates based on profile URL
            unique_profiles = {}
            for profile in all_profiles:
                url = profile.get('profile_url', '')
                if url and url not in unique_profiles:
                    unique_profiles[url] = profile
            
            return list(unique_profiles.values())[:limit]
            
        except Exception as e:
            logger.error(f"Error searching MRM professionals for {bank_name}: {e}")
            return []
    
    def _search_linkedin_people(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Perform LinkedIn people search"""
        try:
            # Navigate to LinkedIn search
            search_url = f"https://www.linkedin.com/search/results/people/?keywords={query.replace(' ', '%20')}"
            self.driver.get(search_url)
            
            # Wait for search results
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "search-results-container")))
            
            profiles = []
            
            # Find profile elements
            profile_elements = self.driver.find_elements(By.CSS_SELECTOR, ".reusable-search__result-container")
            
            for element in profile_elements[:limit]:
                try:
                    profile_data = self._extract_profile_data(element)
                    if profile_data and self._is_mrm_relevant(profile_data):
                        profiles.append(profile_data)
                except Exception as e:
                    logger.warning(f"Error extracting profile data: {e}")
                    continue
            
            return profiles
            
        except Exception as e:
            logger.error(f"Error performing LinkedIn search: {e}")
            return []
    
    def _extract_profile_data(self, element) -> Optional[Dict[str, Any]]:
        """Extract profile data from search result element"""
        try:
            profile_data = {}
            
            # Extract name
            name_element = element.find_element(By.CSS_SELECTOR, ".entity-result__title-text a")
            profile_data['name'] = name_element.text.strip()
            profile_data['profile_url'] = name_element.get_attribute('href')
            
            # Extract current title and company
            try:
                title_element = element.find_element(By.CSS_SELECTOR, ".entity-result__primary-subtitle")
                profile_data['title'] = title_element.text.strip()
            except NoSuchElementException:
                profile_data['title'] = ""
            
            # Extract location
            try:
                location_element = element.find_element(By.CSS_SELECTOR, ".entity-result__secondary-subtitle")
                profile_data['location'] = location_element.text.strip()
            except NoSuchElementException:
                profile_data['location'] = ""
            
            return profile_data
            
        except Exception as e:
            logger.warning(f"Error extracting profile data: {e}")
            return None
    
    def _is_mrm_relevant(self, profile_data: Dict[str, Any]) -> bool:
        """Check if profile is relevant to MRM"""
        title = profile_data.get('title', '').lower()
        name = profile_data.get('name', '').lower()
        
        # Check for MRM keywords in title
        for keyword in MRM_KEYWORDS:
            if keyword.lower() in title:
                return True
        
        # Check for leadership patterns
        for pattern in LEADERSHIP_PATTERNS:
            if re.search(pattern, title, re.IGNORECASE):
                return True
        
        return False
    
    def get_detailed_profile(self, profile_url: str) -> Optional[Dict[str, Any]]:
        """Get detailed information from a LinkedIn profile"""
        if not self.logged_in:
            logger.error("Not logged into LinkedIn")
            return None
        
        try:
            self.driver.get(profile_url)
            
            # Wait for profile to load
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "pv-text-details__left-panel")))
            
            profile_data = {}
            
            # Extract name
            try:
                name_element = self.driver.find_element(By.CSS_SELECTOR, ".text-heading-xlarge")
                profile_data['name'] = name_element.text.strip()
            except NoSuchElementException:
                pass
            
            # Extract current position
            try:
                title_element = self.driver.find_element(By.CSS_SELECTOR, ".text-body-medium.break-words")
                profile_data['title'] = title_element.text.strip()
            except NoSuchElementException:
                pass
            
            # Extract experience section
            try:
                experience_section = self.driver.find_element(By.ID, "experience")
                experience_items = experience_section.find_elements(By.CSS_SELECTOR, ".pvs-list__item--line-separated")
                
                experiences = []
                for item in experience_items[:5]:  # Get top 5 experiences
                    try:
                        exp_data = self._extract_experience_data(item)
                        if exp_data:
                            experiences.append(exp_data)
                    except Exception as e:
                        logger.warning(f"Error extracting experience: {e}")
                        continue
                
                profile_data['experiences'] = experiences
                
            except NoSuchElementException:
                profile_data['experiences'] = []
            
            return profile_data
            
        except Exception as e:
            logger.error(f"Error getting detailed profile from {profile_url}: {e}")
            return None
    
    def _extract_experience_data(self, element) -> Optional[Dict[str, Any]]:
        """Extract experience data from profile element"""
        try:
            exp_data = {}
            
            # Extract job title
            try:
                title_element = element.find_element(By.CSS_SELECTOR, ".mr1.t-bold span")
                exp_data['title'] = title_element.text.strip()
            except NoSuchElementException:
                return None
            
            # Extract company
            try:
                company_element = element.find_element(By.CSS_SELECTOR, ".t-14.t-normal span")
                exp_data['company'] = company_element.text.strip()
            except NoSuchElementException:
                exp_data['company'] = ""
            
            # Extract duration
            try:
                duration_element = element.find_element(By.CSS_SELECTOR, ".pvs-entity__caption-wrapper span")
                exp_data['duration'] = duration_element.text.strip()
            except NoSuchElementException:
                exp_data['duration'] = ""
            
            return exp_data
            
        except Exception as e:
            logger.warning(f"Error extracting experience data: {e}")
            return None
    
    def collect_bank_leadership(self, bank_name: str) -> List[LeadershipInfo]:
        """Collect MRM leadership information for a specific bank"""
        if not self.username or not self.password:
            logger.warning(f"LinkedIn credentials not available, skipping {bank_name}")
            return []
        
        try:
            # Login if not already logged in
            if not self.logged_in:
                login_success = asyncio.run(self.login())
                if not login_success:
                    return []
            
            # Search for MRM professionals
            profiles = self.search_mrm_professionals(bank_name)
            leadership_info = []
            
            for profile in profiles:
                try:
                    # Get detailed profile information
                    detailed_profile = self.get_detailed_profile(profile['profile_url'])
                    
                    if detailed_profile:
                        # Create LeadershipInfo object
                        leader = LeadershipInfo(
                            name=detailed_profile.get('name', profile.get('name', '')),
                            title=detailed_profile.get('title', profile.get('title', '')),
                            linkedin_url=profile['profile_url'],
                            confidence_score=0.7,  # Medium confidence for LinkedIn data
                            source=DataSource.LINKEDIN,
                            last_verified=datetime.utcnow(),
                            notes=f"Found via LinkedIn search for '{bank_name}' MRM professionals"
                        )
                        
                        leadership_info.append(leader)
                    
                    # Add delay between profile requests
                    time.sleep(settings.SCRAPING_DELAY * 3)
                    
                except Exception as e:
                    logger.warning(f"Error processing profile {profile.get('profile_url', 'unknown')}: {e}")
                    continue
            
            logger.info(f"Collected {len(leadership_info)} LinkedIn profiles for {bank_name}")
            return leadership_info
            
        except Exception as e:
            logger.error(f"Error collecting LinkedIn data for {bank_name}: {e}")
            return []
    
    def close(self):
        """Close the browser driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.logged_in = False
            logger.info("LinkedIn collector closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# Async function for easy usage
async def collect_linkedin_data(bank_name: str, username: str = None, password: str = None) -> List[LeadershipInfo]:
    """Convenience function to collect LinkedIn data for a bank"""
    with LinkedInCollector(username, password) as collector:
        return collector.collect_bank_leadership(bank_name)

# Global collector instance
linkedin_collector = LinkedInCollector()