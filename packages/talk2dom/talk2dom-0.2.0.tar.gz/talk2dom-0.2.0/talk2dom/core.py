import logging
import time
from pydantic import BaseModel, Field

from bs4 import BeautifulSoup

from langchain.chat_models import init_chat_model
from langchain_core.output_parsers.openai_tools import PydanticToolsParser

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By

from pathlib import Path


LOGGER = logging.getLogger(__name__)


def load_prompt(file_path: str) -> str:
    prompt_path = Path(__file__).parent / "prompts" / file_path
    return prompt_path.read_text(encoding="utf-8").strip()


# ------------------ Pydantic Schema ------------------


class Selector(BaseModel):
    selector_type: str = Field(
        description="Either 'id', 'tag name', 'name', 'class name', 'xpath' or 'css selector'"
    )
    selector_value: str = Field(description="The selector string")


tools = [Selector]


# ------------------ LLM Function Call ------------------


def call_llm(
    user_instruction, html, model, model_provider, conversation_history=None
) -> Selector:
    llm = init_chat_model(model, model_provider=model_provider)
    chain = llm.bind_tools(tools) | PydanticToolsParser(tools=tools)

    query = load_prompt("locator_prompt.txt")
    if conversation_history:
        query += "\n\n## Conversation History:"
        for user_message, assistant_message in conversation_history:
            query += f"\n\nUser: {user_message}\n\nAssistant: {assistant_message}"
    query += f"\n\n## HTML: \n{html}\n\nUser: {user_instruction}\n\nAssistant:"
    print(query)
    response = chain.invoke(query)[0]
    return response


def highlight_element(driver, element, duration=2):
    style = (
        "box-shadow: 0 0 10px 3px rgba(255, 0, 0, 0.7);"
        "outline: 2px solid red;"
        "background-color: rgba(255, 230, 200, 0.3);"
        "transition: all 0.2s ease-in-out;"
    )
    original_style = element.get_attribute("style")
    driver.execute_script(f"arguments[0].setAttribute('style', '{style}')", element)
    if duration:
        time.sleep(duration)
        driver.execute_script(
            f"arguments[0].setAttribute('style', `{original_style}`)", element
        )


# ------------------ Public API ------------------


def get_locator(
    element,
    description,
    model="gpt-4o-mini",
    model_provider="openai",
    conversation_history=None,
):
    """
    Get the locator for the element using LLM.
    :param element: The element to locate.
    :param description: The description of the element.
    :param model: The model to use for the LLM.
    :param model_provider: The model provider to use for the LLM.
    :param conversation_history: The conversation history to use for the LLM.
    :return: The locator type and value.
    """
    html = (
        element.find_element(By.TAG_NAME, "body").get_attribute("outerHTML")
        if isinstance(element, WebDriver)
        else element.get_attribute("outerHTML")
    )
    soup = BeautifulSoup(html, "lxml")

    # remove unnecessary tags
    for tag in soup(["script", "style", "meta", "link"]):
        tag.decompose()

    html = soup.prettify()

    selector = call_llm(description, html, model, model_provider, conversation_history)

    if selector.selector_type not in [
        "id",
        "tag name",
        "name",
        "class name",
        "xpath",
        "css selector",
    ]:
        raise ValueError(f"Unsupported selector type: {selector.selector_type}")

    LOGGER.info(
        "Located by: %s, selector: %s", selector.selector_type, selector.selector_value
    )
    return selector.selector_type, selector.selector_value.strip()


def get_element(
    driver,
    description,
    element=None,
    model="gpt-4o-mini",
    model_provider="openai",
    duration=None,
    conversation_history=None,
):
    """
    Get the element using LLM.
    :param driver: The WebDriver instance.
    :param description: The description of the element.
    :param element: The element to locate.
    :param model: The model to use for the LLM.
    :param model_provider: The model provider to use for the LLM.
    :param duration: The duration to highlight the element.
    :param conversation_history: The conversation history to use for the LLM.
    :return: The located element.
    """
    if element is None:
        selector_type, selector_value = get_locator(
            driver, description, model, model_provider, conversation_history
        )
    else:
        selector_type, selector_value = get_locator(
            element, description, model, model_provider, conversation_history
        )
    elem = driver.find_element(
        selector_type, selector_value
    )  # Ensure the page is loaded
    highlight_element(driver, elem, duration=duration)
    return elem
