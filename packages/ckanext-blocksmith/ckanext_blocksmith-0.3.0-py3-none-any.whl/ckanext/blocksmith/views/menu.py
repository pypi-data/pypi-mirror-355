from flask import Blueprint
from flask.views import MethodView

import ckan.plugins.toolkit as tk
from ckan.types import Context

import ckanext.blocksmith.model as model

bs_menu_blueprint = Blueprint("bs_menu", __name__, url_prefix="/blocksmith")


def make_context() -> Context:
    return {
        "user": tk.current_user.name,
        "auth_user_obj": tk.current_user,
    }


class MenuListView(MethodView):
    def get(self):
        try:
            tk.check_access("blocksmith_manage_menu", make_context(), {})
        except tk.NotAuthorized:
            return tk.abort(404, "You are not authorized to visit this page")

        menus = [menu.dictize({}) for menu in model.MenuModel.get_all()]

        return tk.render("blocksmith/menu/menu_list.html", extra_vars={"menus": menus})

    # def post(self):
    #     return tk.render("blocksmith/menu/menu_list.html")


class MenuItems(MethodView):
    def get(self, menu_name: str):
        try:
            tk.check_access("blocksmith_manage_menu", make_context(), {})
        except tk.NotAuthorized:
            return tk.abort(404, "You are not authorized to visit this page")

        menu = model.MenuModel.get_by_name(menu_name)

        return tk.render("blocksmith/menu/menu_items.html", extra_vars={"menu": menu})


bs_menu_blueprint.add_url_rule("/menu_list", view_func=MenuListView.as_view("list"))
bs_menu_blueprint.add_url_rule(
    "/menu/<menu_name>", view_func=MenuItems.as_view("items")
)
