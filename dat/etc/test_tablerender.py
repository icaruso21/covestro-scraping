# Generated by Selenium IDE
import pytest
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

class TestTablerender():
  def setup_method(self, method):
    self.driver = webdriver.Chrome()
    self.vars = {}
  
  def teardown_method(self, method):
    self.driver.quit()
  
  def test_tablerender(self):
    self.driver.get("https://solutions.covestro.com/en/products/multranol/multranol-3900_04911806-12983619?SelectedCountry=US")
    self.driver.set_window_size(1440, 877)
    self.driver.find_element(By.CSS_SELECTOR, ".m-table:nth-child(3) .m-table__row:nth-child(4) > .m-table__body-cell:nth-child(1) > span").click()
    self.driver.find_element(By.CSS_SELECTOR, ".m-table:nth-child(3) .m-table__row:nth-child(4) > .m-table__body-cell:nth-child(1) > span").click()
    self.driver.find_element(By.CSS_SELECTOR, ".m-table:nth-child(3) .m-table__row:nth-child(4) > .m-table__body-cell:nth-child(1) > span").click()
    element = self.driver.find_element(By.CSS_SELECTOR, ".m-table:nth-child(3) .m-table__row:nth-child(4) > .m-table__body-cell:nth-child(1) > span")
    actions = ActionChains(self.driver)
    actions.double_click(element).perform()
    self.driver.close()
  
