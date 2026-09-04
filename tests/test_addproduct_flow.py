"""Tests for the /addproduct back-navigation and review flow.

These exercise the conversation handler functions directly with mocked
Telegram Update/Context objects — no real bot connection or database needed,
since these functions are pure state-machine logic until the final
review_confirm step (which touches the DB and is mocked out here).
"""
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.bot.handlers_owner import (
    BRAND,
    CATEGORY,
    COLORS,
    NAME,
    PHOTO,
    PRICE,
    REVIEW,
    SPEC_BATTERY,
    SPEC_PROCESSOR,
    SPEC_RAM,
    SPEC_STORAGE,
    STOCK,
    _review_text,
    add_product_brand,
    add_product_category,
    add_product_colors,
    add_product_name,
    add_product_photo,
    add_product_price,
    add_product_spec_battery,
    add_product_spec_processor,
    add_product_spec_ram,
    add_product_spec_storage,
    add_product_start,
    add_product_stock,
)


def make_update(text=None, photo=None):
    """Builds a mock Update with a mock message whose reply_text is an AsyncMock
    we can assert against. effective_user.id is set to match TELEGRAM_OWNER_ID
    (123, per the test env vars) so @owner_only-protected handlers pass."""
    update = MagicMock()
    update.effective_user = MagicMock()
    update.effective_user.id = 123
    update.message = MagicMock()
    update.message.text = text
    update.message.photo = photo or []
    update.message.reply_text = AsyncMock()
    return update


def make_context():
    context = MagicMock()
    context.user_data = {}
    return context


@pytest.mark.asyncio
async def test_forward_flow_phone_reaches_ram_spec_step():
    update = make_update()
    context = make_context()

    state = await add_product_start(update, context)
    assert state == NAME

    update.message.text = "Samsung Galaxy A15"
    state = await add_product_name(update, context)
    assert state == CATEGORY
    assert context.user_data["new_product"]["name"] == "Samsung Galaxy A15"

    update.message.text = "phone"
    state = await add_product_category(update, context)
    assert state == BRAND
    assert context.user_data["new_product"]["category"] == "phone"

    update.message.text = "Samsung"
    state = await add_product_brand(update, context)
    assert state == PRICE

    update.message.text = "15000"
    state = await add_product_price(update, context)
    assert state == COLORS
    assert context.user_data["new_product"]["price"] == 15000.0

    update.message.text = "Black, Blue"
    state = await add_product_colors(update, context)
    assert state == STOCK
    assert context.user_data["new_product"]["colors"] == ["Black", "Blue"]

    update.message.text = "5"
    state = await add_product_stock(update, context)
    assert state == SPEC_RAM
    assert context.user_data["new_product"]["stock_qty"] == 5


@pytest.mark.asyncio
async def test_back_from_brand_returns_to_category_and_resends_prompt():
    update = make_update()
    context = make_context()
    context.user_data["new_product"] = {"name": "Test Phone"}

    update.message.text = "back"
    state = await add_product_brand(update, context)

    assert state == CATEGORY
    update.message.reply_text.assert_awaited_once()
    call_args = update.message.reply_text.call_args
    assert "Category?" in call_args[0][0]


@pytest.mark.asyncio
async def test_back_from_price_returns_to_brand():
    update = make_update()
    context = make_context()
    context.user_data["new_product"] = {"name": "X", "category": "phone"}

    update.message.text = "back"
    state = await add_product_price(update, context)

    assert state == BRAND
    call_args = update.message.reply_text.call_args
    assert "Brand?" in call_args[0][0]


@pytest.mark.asyncio
async def test_back_chain_through_spec_steps():
    """Simulates typing 'back' repeatedly through the phone spec steps and
    confirms each step lands on the correct previous state."""
    context = make_context()
    context.user_data["new_product"] = {"category": "phone", "specs": {}}

    update = make_update(text="back")
    state = await add_product_spec_battery(update, context)
    assert state == SPEC_PROCESSOR

    update = make_update(text="back")
    state = await add_product_spec_processor(update, context)
    assert state == SPEC_STORAGE

    update = make_update(text="back")
    state = await add_product_spec_storage(update, context)
    assert state == SPEC_RAM

    update = make_update(text="back")
    state = await add_product_spec_ram(update, context)
    assert state == STOCK


@pytest.mark.asyncio
async def test_full_spec_collection_populates_specs_dict():
    context = make_context()
    context.user_data["new_product"] = {"category": "phone", "specs": {}}

    update = make_update(text="8GB")
    state = await add_product_spec_ram(update, context)
    assert state == SPEC_STORAGE

    update = make_update(text="128GB")
    state = await add_product_spec_storage(update, context)
    assert state == SPEC_PROCESSOR

    update = make_update(text="Snapdragon 8 Gen 3")
    state = await add_product_spec_processor(update, context)
    assert state == SPEC_BATTERY

    update = make_update(text="5000mAh")
    state = await add_product_spec_battery(update, context)
    assert state == PHOTO

    specs = context.user_data["new_product"]["specs"]
    assert specs == {
        "ram": "8GB",
        "storage": "128GB",
        "processor": "Snapdragon 8 Gen 3",
        "battery": "5000mAh",
    }


@pytest.mark.asyncio
async def test_photo_step_skip_reaches_review_with_no_photo():
    context = make_context()
    context.user_data["new_product"] = {
        "name": "Galaxy A15",
        "category": "phone",
        "brand": "Samsung",
        "price": 15000.0,
        "colors": ["Black"],
        "stock_qty": 5,
        "specs": {"ram": "8GB"},
    }
    update = make_update(text="skip")

    state = await add_product_photo(update, context)

    assert state == REVIEW
    update.message.reply_text.assert_awaited_once()
    review_message = update.message.reply_text.call_args[0][0]
    assert "Galaxy A15" in review_message
    assert "Samsung" in review_message
    assert "Photo: none yet" in review_message


def test_review_text_includes_photo_confirmation_when_present():
    data = {
        "name": "iPhone 15",
        "category": "phone",
        "brand": "Apple",
        "price": 60000,
        "colors": ["Black", "White"],
        "stock_qty": 3,
        "specs": {"ram": "6GB", "storage": "128GB"},
        "photo_urls": ["https://example.com/photo.jpg"],
    }
    text = _review_text(data)

    assert "iPhone 15" in text
    assert "Apple" in text
    assert "Ram: 6GB" in text
    assert "Storage: 128GB" in text
    assert "Photo: ✅ attached" in text