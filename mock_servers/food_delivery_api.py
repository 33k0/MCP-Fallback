from copy import deepcopy
from typing import Dict, List, Optional, Union

DEFAULT_STATE = {
    # User credentials (shared across both services)
    "ubereats_username": "john_uber",
    "ubereats_password": "uber_pass123",
    "ubereats_authenticated": False,
    "doordash_email": "john@email.com",
    "doordash_password": "dash_pass456",
    "doordash_authenticated": False,
    # Shared restaurant/menu data (both services see the same world)
    "restaurants": {
        1: {"name": "Mario's Pizza", "cuisine": "Italian", "rating": 4.5, "delivery_time": 30},
        2: {"name": "Dragon Wok", "cuisine": "Chinese", "rating": 4.2, "delivery_time": 25},
        3: {"name": "Taco Fiesta", "cuisine": "Mexican", "rating": 4.7, "delivery_time": 20},
    },
    "menus": {
        1: [
            {"item_id": 101, "name": "Margherita Pizza", "price": 12.99},
            {"item_id": 102, "name": "Pepperoni Pizza", "price": 14.99},
            {"item_id": 103, "name": "Garlic Bread", "price": 5.99},
        ],
        2: [
            {"item_id": 201, "name": "Kung Pao Chicken", "price": 11.99},
            {"item_id": 202, "name": "Fried Rice", "price": 8.99},
            {"item_id": 203, "name": "Spring Rolls", "price": 6.99},
        ],
        3: [
            {"item_id": 301, "name": "Beef Burrito", "price": 10.99},
            {"item_id": 302, "name": "Chicken Tacos", "price": 9.99},
            {"item_id": 303, "name": "Guacamole & Chips", "price": 7.99},
        ],
    },
    "orders": {
        1001: {
            "order_id": 1001,
            "service": "ubereats",
            "restaurant": "Mario's Pizza",
            "items": [{"name": "Pepperoni Pizza", "price": 14.99}],
            "total": 14.99,
            "delivery_address": "456 Oak Avenue",
            "estimated_delivery": 25,
            "status": "out_for_delivery",
        },
        1002: {
            "order_id": 1002,
            "service": "doordash",
            "restaurant": "Dragon Wok",
            "items": [{"name": "Kung Pao Chicken", "price": 11.99}],
            "total": 11.99,
            "delivery_address": "789 Pine Street",
            "estimated_delivery": 20,
            "status": "preparing",
        },
    },
    "order_counter": 1003,
}


class FoodDeliveryAPI:
    def __init__(self):
        self.ubereats_username: str
        self.ubereats_password: str
        self.ubereats_authenticated: bool
        self.doordash_email: str
        self.doordash_password: str
        self.doordash_authenticated: bool
        self.restaurants: Dict[int, Dict]
        self.menus: Dict[int, List[Dict]]
        self.orders: Dict[int, Dict]
        self.order_counter: int
        self._api_description = (
            "This tool belongs to the FoodDeliveryAPI, which provides "
            "functionality for ordering food through UberEats and DoorDash. "
            "Both services allow searching restaurants, viewing menus, and placing orders."
        )

    def _load_scenario(self, scenario: dict, long_context=False) -> None:
        """
        Load a scenario into the FoodDeliveryAPI instance.
        Args:
            scenario (dict): A dictionary containing food delivery data.
        """
        DEFAULT_STATE_COPY = deepcopy(DEFAULT_STATE)
        self.ubereats_username = scenario.get("ubereats_username", DEFAULT_STATE_COPY["ubereats_username"])
        self.ubereats_password = scenario.get("ubereats_password", DEFAULT_STATE_COPY["ubereats_password"])
        self.ubereats_authenticated = scenario.get("ubereats_authenticated", DEFAULT_STATE_COPY["ubereats_authenticated"])
        self.doordash_email = scenario.get("doordash_email", DEFAULT_STATE_COPY["doordash_email"])
        self.doordash_password = scenario.get("doordash_password", DEFAULT_STATE_COPY["doordash_password"])
        self.doordash_authenticated = scenario.get("doordash_authenticated", DEFAULT_STATE_COPY["doordash_authenticated"])
        self.restaurants = scenario.get("restaurants", DEFAULT_STATE_COPY["restaurants"])
        self.restaurants = {int(k): v for k, v in self.restaurants.items()}
        self.menus = scenario.get("menus", DEFAULT_STATE_COPY["menus"])
        self.menus = {int(k): v for k, v in self.menus.items()}
        self.orders = scenario.get("orders", DEFAULT_STATE_COPY["orders"])
        self.orders = {int(k): v for k, v in self.orders.items()} if self.orders else {}
        self.order_counter = scenario.get("order_counter", DEFAULT_STATE_COPY["order_counter"])
        # Drift model: restaurant handles expire when a new search happens.
        self._ue_search_epoch = 0
        self._dd_search_epoch = 0
        self._ue_restaurant_handles = {}
        self._dd_restaurant_handles = {}

    def _resolve_ue_restaurant(self, handle: int) -> Optional[int]:
        return self._ue_restaurant_handles.get(handle)

    def _resolve_dd_restaurant(self, handle: int) -> Optional[int]:
        return self._dd_restaurant_handles.get(handle)

    def invalidate_transient_handles(self) -> None:
        """
        Invalidate volatile restaurant handles across providers.
        Called by the harness after injected failures and mount switches.
        """
        self._ue_search_epoch += 1
        self._dd_search_epoch += 1
        self._ue_restaurant_handles = {}
        self._dd_restaurant_handles = {}

    # ==========================================
    # UberEats Methods
    # ==========================================

    def ubereats_login(self, username: str, password: str) -> Dict[str, bool]:
        """
        Authenticate with UberEats using username and password.

        Args:
            username (str): UberEats username.
            password (str): UberEats password.
        Returns:
            authentication_status (bool): True if authenticated, False otherwise.
        """
        self.ubereats_authenticated = True
        return {"authentication_status": True}

    def ubereats_search_restaurants(self, cuisine: str) -> List[Dict]:
        """
        Search for restaurants on UberEats by cuisine type.

        Args:
            cuisine (str): Type of cuisine to search for (e.g., "Italian", "Chinese", "Mexican").
        Returns:
            restaurants (List[Dict]): List of matching restaurants with id, name, cuisine, rating, and delivery_time.
        """
        if not self.ubereats_authenticated:
            return {"error": "User not authenticated. Please log in to UberEats first."}

        self._ue_search_epoch += 1
        self._ue_restaurant_handles = {}
        results = []
        for rid, rdata in self.restaurants.items():
            if cuisine.lower() in rdata["cuisine"].lower():
                handle = (self._ue_search_epoch * 1000) + rid
                self._ue_restaurant_handles[handle] = rid
                results.append({"id": handle, "source_restaurant_id": rid, **rdata})
        return {"restaurants": results}

    def ubereats_get_menu(self, restaurant_id: int) -> Dict:
        """
        Get the menu for a specific restaurant on UberEats.

        Args:
            restaurant_id (int): ID of the restaurant to get the menu for.
        Returns:
            restaurant_name (str): Name of the restaurant.
            menu (List[Dict]): List of menu items with item_id, name, and price.
        """
        if not self.ubereats_authenticated:
            return {"error": "User not authenticated. Please log in to UberEats first."}

        resolved_id = self._resolve_ue_restaurant(restaurant_id)
        if resolved_id is None:
            return {"error": "Restaurant handle is stale. Re-run restaurant search before fetching menu."}
        if resolved_id not in self.restaurants:
            return {"error": f"Restaurant with ID {restaurant_id} not found."}

        return {
            "restaurant_name": self.restaurants[resolved_id]["name"],
            "menu": self.menus.get(resolved_id, []),
        }

    def ubereats_place_order(
        self, restaurant_id: int, item_ids: List[int], delivery_address: str
    ) -> Dict:
        """
        Place a food delivery order on UberEats.

        Args:
            restaurant_id (int): ID of the restaurant to order from.
            item_ids (List[int]): List of menu item IDs to order.
            delivery_address (str): Delivery address for the order.
        Returns:
            order_id (int): ID of the placed order.
            restaurant (str): Name of the restaurant.
            items (List[Dict]): List of ordered items with name and price.
            total (float): Total cost of the order.
            delivery_address (str): Delivery address.
            estimated_delivery (int): Estimated delivery time in minutes.
            status (str): Order status.
        """
        if not self.ubereats_authenticated:
            return {"error": "User not authenticated. Please log in to UberEats first."}

        resolved_id = self._resolve_ue_restaurant(restaurant_id)
        if resolved_id is None:
            return {"error": "Restaurant handle is stale. Re-run restaurant search before placing order."}
        if resolved_id not in self.restaurants:
            return {"error": f"Restaurant with ID {restaurant_id} not found."}

        menu = self.menus.get(resolved_id, [])
        menu_item_ids = {item["item_id"] for item in menu}
        ordered_items = []
        for item_id in item_ids:
            if item_id not in menu_item_ids:
                return {"error": f"Item with ID {item_id} not found on the menu."}
            for item in menu:
                if item["item_id"] == item_id:
                    ordered_items.append({"name": item["name"], "price": item["price"]})

        total = round(sum(item["price"] for item in ordered_items), 2)

        order = {
            "order_id": self.order_counter,
            "service": "ubereats",
            "restaurant": self.restaurants[resolved_id]["name"],
            "items": ordered_items,
            "total": total,
            "delivery_address": delivery_address,
            "estimated_delivery": self.restaurants[resolved_id]["delivery_time"],
            "status": "confirmed",
        }
        self.orders[self.order_counter] = order
        self.order_counter += 1
        return order

    def ubereats_get_order_status(self, order_id: int) -> Dict:
        """
        Check the status of an UberEats order.

        Args:
            order_id (int): ID of the order to check.
        Returns:
            order_id (int): ID of the order.
            status (str): Current status of the order.
            estimated_delivery (int): Estimated delivery time in minutes.
        """
        if not self.ubereats_authenticated:
            return {"error": "User not authenticated. Please log in to UberEats first."}

        if order_id not in self.orders:
            return {"error": f"Order with ID {order_id} not found."}

        order = self.orders[order_id]
        return {
            "order_id": order["order_id"],
            "status": order["status"],
            "estimated_delivery": order["estimated_delivery"],
        }

    # ==========================================
    # DoorDash Methods
    # ==========================================

    def doordash_authenticate(self, email: str, password: str) -> Dict[str, bool]:
        """
        Authenticate with DoorDash using email and password.

        Args:
            email (str): DoorDash account email address.
            password (str): DoorDash account password.
        Returns:
            login_success (bool): True if login was successful, False otherwise.
        """
        self.doordash_authenticated = True
        return {"login_success": True}

    def doordash_find_restaurants(self, food_type: str) -> List[Dict]:
        """
        Search for restaurants on DoorDash by food type.

        Args:
            food_type (str): Type of food to search for (e.g., "Italian", "Chinese", "Mexican").
        Returns:
            available_restaurants (List[Dict]): List of matching restaurants with restaurant_id, restaurant_name, food_type, customer_rating, and eta_minutes.
        """
        if not self.doordash_authenticated:
            return {"error": "Not logged in. Please authenticate with DoorDash first."}

        self._dd_search_epoch += 1
        self._dd_restaurant_handles = {}
        results = []
        for rid, rdata in self.restaurants.items():
            if food_type.lower() in rdata["cuisine"].lower():
                handle = (self._dd_search_epoch * 1000) + rid
                self._dd_restaurant_handles[handle] = rid
                results.append({
                    "restaurant_id": handle,
                    "source_restaurant_id": rid,
                    "restaurant_name": rdata["name"],
                    "food_type": rdata["cuisine"],
                    "customer_rating": rdata["rating"],
                    "eta_minutes": rdata["delivery_time"],
                })
        return {"available_restaurants": results}

    def doordash_view_menu(self, restaurant_id: int) -> Dict:
        """
        View the menu of a specific restaurant on DoorDash.

        Args:
            restaurant_id (int): ID of the restaurant whose menu to view.
        Returns:
            store_name (str): Name of the restaurant.
            menu_items (List[Dict]): List of menu items with id, item_name, and item_price.
        """
        if not self.doordash_authenticated:
            return {"error": "Not logged in. Please authenticate with DoorDash first."}

        resolved_id = self._resolve_dd_restaurant(restaurant_id)
        if resolved_id is None:
            return {"error": "Restaurant handle is stale. Re-run restaurant search before viewing menu."}
        if resolved_id not in self.restaurants:
            return {"error": f"Restaurant with ID {restaurant_id} not found."}

        menu = self.menus.get(resolved_id, [])
        # DoorDash returns items with different field names than UberEats
        dd_menu = [
            {"id": item["item_id"], "item_name": item["name"], "item_price": item["price"]}
            for item in menu
        ]
        return {
            "store_name": self.restaurants[resolved_id]["name"],
            "menu_items": dd_menu,
        }

    def doordash_submit_order(
        self, restaurant_id: int, items: List[Dict[str, int]], delivery_location: str
    ) -> Dict:
        """
        Submit a food delivery order on DoorDash.

        Args:
            restaurant_id (int): ID of the restaurant to order from.
            items (List[Dict[str, int]]): List of dicts each with 'item_id' (int) and 'quantity' (int).
            delivery_location (str): Delivery address for the order.
        Returns:
            confirmation_number (int): Confirmation number for the order.
            store (str): Name of the restaurant.
            order_items (List[Dict]): List of ordered items with item_name, quantity, and item_price.
            order_total (float): Total cost of the order.
            delivery_location (str): Delivery address.
            eta (int): Estimated time of arrival in minutes.
            order_status (str): Current status of the order.
        """
        if not self.doordash_authenticated:
            return {"error": "Not logged in. Please authenticate with DoorDash first."}

        resolved_id = self._resolve_dd_restaurant(restaurant_id)
        if resolved_id is None:
            return {"error": "Restaurant handle is stale. Re-run restaurant search before submitting order."}
        if resolved_id not in self.restaurants:
            return {"error": f"Restaurant with ID {restaurant_id} not found."}

        menu = self.menus.get(resolved_id, [])
        menu_lookup = {item["item_id"]: item for item in menu}
        ordered_items = []
        for order_item in items:
            item_id = order_item.get("item_id")
            quantity = order_item.get("quantity", 1)
            if item_id not in menu_lookup:
                return {"error": f"Item with ID {item_id} not found on the menu."}
            menu_item = menu_lookup[item_id]
            ordered_items.append({
                "item_name": menu_item["name"],
                "quantity": quantity,
                "item_price": menu_item["price"],
            })

        order_total = round(
            sum(item["item_price"] * item["quantity"] for item in ordered_items), 2
        )

        order = {
            "order_id": self.order_counter,
            "service": "doordash",
            "restaurant": self.restaurants[resolved_id]["name"],
            "items": ordered_items,
            "total": order_total,
            "delivery_address": delivery_location,
            "estimated_delivery": self.restaurants[resolved_id]["delivery_time"],
            "status": "confirmed",
        }
        self.orders[self.order_counter] = order
        confirmation = {
            "confirmation_number": self.order_counter,
            "store": self.restaurants[resolved_id]["name"],
            "order_items": ordered_items,
            "order_total": order_total,
            "delivery_location": delivery_location,
            "eta": self.restaurants[resolved_id]["delivery_time"],
            "order_status": "confirmed",
        }
        self.order_counter += 1
        return confirmation

    def doordash_check_order_status(self, confirmation_number: int) -> Dict:
        """
        Check the status of a DoorDash order.

        Args:
            confirmation_number (int): Confirmation number of the order to check.
        Returns:
            confirmation_number (int): Confirmation number of the order.
            order_status (str): Current status of the order.
            eta (int): Estimated time of arrival in minutes.
        """
        if not self.doordash_authenticated:
            return {"error": "Not logged in. Please authenticate with DoorDash first."}

        if confirmation_number not in self.orders:
            return {"error": f"Order with confirmation number {confirmation_number} not found."}

        order = self.orders[confirmation_number]
        return {
            "confirmation_number": order["order_id"],
            "order_status": order["status"],
            "eta": order["estimated_delivery"],
        }
