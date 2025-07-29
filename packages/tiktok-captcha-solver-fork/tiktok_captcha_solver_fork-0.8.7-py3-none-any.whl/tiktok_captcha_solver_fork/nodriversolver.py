"""This class handles the captcha solving for selenium users"""

import time
from typing import Literal

from selenium.webdriver import ActionChains, Chrome
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from undetected_chromedriver import logging
from undetected_chromedriver.patcher import random

from zendriver import Tab

from tiktok_captcha_solver.asyncsolver import AsyncSolver

from .api import ApiClient
from .downloader import fetch_image_b64
from .solver import Solver


class NodriverSolver(AsyncSolver):

    client: ApiClient
    tab: Tab

    def __init__(
            self,
            tab: Tab,
            sadcaptcha_api_key: str,
            headers: dict | None = None,
            proxy: str | None = None
        ) -> None:
        self.tab = tab
        self.client = ApiClient(sadcaptcha_api_key)
        self.headers = headers
        self.proxy = proxy

    async def captcha_is_present(self, timeout: int = 15) -> bool:
        for _ in range(timeout * 2):
            if await self._any_selector_in_list_present(self.captcha_wrappers):
                print("Captcha detected")
                return True
            time.sleep(0.5)
        logging.debug("Captcha not found")
        return False

    async def captcha_is_not_present(self, timeout: int = 15) -> bool:
        for _ in range(timeout * 2):
            if len(self.tab.find_elements(By.CSS_SELECTOR, self.captcha_wrappers[0])) == 0:
                print("Captcha detected")
                return True
            time.sleep(0.5)
        logging.debug("Captcha not found")
        return False

    async def identify_captcha(self) -> Literal["puzzle", "shapes", "rotate"]:
        for _ in range(15):
            if self._any_selector_in_list_present(self.puzzle_selectors):
                return "puzzle"
            elif self._any_selector_in_list_present(self.rotate_selectors):
                return "rotate"
            elif self._any_selector_in_list_present(self.shapes_selectors):
                return "shapes"
            else:
                time.sleep(2)
        raise ValueError("Neither puzzle, shapes, or rotate captcha was present.")

    async def solve_shapes(self) -> None:
        if not self._any_selector_in_list_present(["#captcha-verify-image"]):
            logging.debug("Went to solve puzzle but #captcha-verify-image was not present")
            return
        image = fetch_image_b64(self._get_shapes_image_url(), headers=self.headers, proxy=self.proxy)
        solution = self.client.shapes(image)
        image_element = self.tab.find_element(By.CSS_SELECTOR, "#captcha-verify-image")
        self._click_proportional(image_element, solution.point_one_proportion_x, solution.point_one_proportion_y)
        self._click_proportional(image_element, solution.point_two_proportion_x, solution.point_two_proportion_y)
        self.tab.find_element(By.CSS_SELECTOR, ".verify-captcha-submit-button").click()

    async def solve_rotate(self) -> None:
        if not self._any_selector_in_list_present(["[data-testid=whirl-inner-img]"]):
            logging.debug("Went to solve rotate but whirl-inner-img was not present")
            return
        outer = fetch_image_b64(self._get_rotate_outer_image_url(), headers=self.headers, proxy=self.proxy)
        inner = fetch_image_b64(self._get_rotate_inner_image_url(), headers=self.headers, proxy=self.proxy)
        solution = self.client.rotate(outer, inner)
        distance = self._compute_rotate_slide_distance(solution.angle)
        self._drag_element_horizontal(".secsdk-captcha-drag-icon", distance)

    async def solve_puzzle(self) -> None:
        if not self._any_selector_in_list_present(["#captcha-verify-image"]):
            logging.debug("Went to solve puzzle but #captcha-verify-image was not present")
            return
        puzzle = fetch_image_b64(self._get_puzzle_image_url(), headers=self.headers, proxy=self.proxy)
        piece = fetch_image_b64(self._get_piece_image_url(), headers=self.headers, proxy=self.proxy)
        solution = self.client.puzzle(puzzle, piece)
        distance = self._compute_puzzle_slide_distance(solution.slide_x_proportion)
        self._drag_element_horizontal(".secsdk-captcha-drag-icon", distance)

    async def _compute_rotate_slide_distance(self, angle: int) -> int:
        slide_length = self._get_slide_length()
        icon_length = self._get_slide_icon_length()
        return int(((slide_length - icon_length) * angle) / 360)

    async def _compute_puzzle_slide_distance(self, proportion_x: float) -> int:
        e = self.tab.find_element(By.CSS_SELECTOR, "#captcha-verify-image")
        return int(proportion_x * e.size["width"])

    async def _get_slide_length(self) -> int:
        e = self.tab.find_element(By.CSS_SELECTOR, ".captcha_verify_slide--slidebar")
        return e.size['width']

    async def _get_slide_icon_length(self) -> int:
        e = self.tab.find_element(By.CSS_SELECTOR, ".secsdk-captcha-drag-icon")
        return e.size['width']

    async def _get_rotate_inner_image_url(self) -> str:
        e = self.tab.find_element(By.CSS_SELECTOR, "[data-testid=whirl-inner-img]")
        url = e.get_attribute("src")
        if not url:
            raise ValueError("Inner image URL was None")
        return url

    async def _get_rotate_outer_image_url(self) -> str:
        e = self.tab.find_element(By.CSS_SELECTOR, "[data-testid=whirl-outer-img]")
        url = e.get_attribute("src")
        if not url:
            raise ValueError("Outer image URL was None")
        return url

    async def _get_puzzle_image_url(self) -> str:
        e = self.tab.find_element(By.CSS_SELECTOR, "#captcha-verify-image")
        url = e.get_attribute("src")
        if not url:
            raise ValueError("Puzzle image URL was None")
        return url

    async def _get_piece_image_url(self) -> str:
        e = self.tab.find_element(By.CSS_SELECTOR, ".captcha_verify_img_slide")
        url = e.get_attribute("src")
        if not url:
            raise ValueError("Piece image URL was None")
        return url

    async def _get_shapes_image_url(self) -> str:
        e = self.tab.find_element(By.CSS_SELECTOR, "#captcha-verify-image")
        url = e.get_attribute("src")
        if not url:
            raise ValueError("Shapes image URL was None")
        return url

    async def _click_proportional(
            self,
            element: WebElement,
            proportion_x: float,
            proportion_y: float
        ) -> None:
        """Click an element inside its bounding box at a point defined by the proportions of x and y
        to the width and height of the entire element

        Args:
            element: WebElement to click inside
            proportion_x: float from 0 to 1 defining the proportion x location to click
            proportion_y: float from 0 to 1 defining the proportion y location to click
        """
        x_origin = element.location["x"]
        y_origin = element.location["y"]
        x_offset = (proportion_x * element.size["width"])
        y_offset = (proportion_y * element.size["height"])
        action = ActionBuilder(self.tab)
        action.pointer_action \
            .move_to_location(x_origin + x_offset, y_origin + y_offset) \
            .pause(random.randint(1, 10) / 11) \
            .click() \
            .pause(random.randint(1, 10) / 11)
        action.perform()

    async def _drag_element_horizontal(self, css_selector: str, x: int) -> None:
        e = self.tab.find_element(By.CSS_SELECTOR, css_selector)
        actions = ActionChains(self.tab, duration=0)
        actions.click_and_hold(e)
        time.sleep(0.1)
        for _ in range(0, x - 15):
            actions.move_by_offset(1, 0)
        for _ in range(0, 20):
            actions.move_by_offset(1, 0)
            actions.pause(0.01)
        actions.pause(0.7)
        for _ in range(0, 5):
            actions.move_by_offset(-1, 0)
            actions.pause(0.05)
        actions.pause(0.1)
        actions.release().perform()

    async def _any_selector_in_list_present(self, selectors: list[str]) -> bool:
        for selector in selectors:
            for ele in self.tab.find_elements(By.CSS_SELECTOR, selector):
                if ele.is_displayed():
                    logging.debug("Detected selector: " + selector + " from list " + ", ".join(selectors))
                    return True
        logging.debug("No selector in list found: " + ", ".join(selectors))
        return False
