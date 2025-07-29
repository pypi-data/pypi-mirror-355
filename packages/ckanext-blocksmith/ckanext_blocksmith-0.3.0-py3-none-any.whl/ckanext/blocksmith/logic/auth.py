import ckan.plugins.toolkit as tk
from ckan.types import AuthResult, Context, DataDict

import ckanext.blocksmith.model as model


def blocksmith_create_page(context: Context, data_dict: DataDict) -> AuthResult:
    return {"success": False}


def blocksmith_edit_page(context: Context, data_dict: DataDict) -> AuthResult:
    return {"success": False}


def blocksmith_update_page(context: Context, data_dict: DataDict) -> AuthResult:
    return {"success": False}


def blocksmith_list_pages(context: Context, data_dict: DataDict) -> AuthResult:
    return {"success": False}


def blocksmith_delete_page(context: Context, data_dict: DataDict) -> AuthResult:
    return {"success": False}


def blocksmith_create_snippet(context: Context, data_dict: DataDict) -> AuthResult:
    return {"success": False}


def blocksmith_edit_snippet(context: Context, data_dict: DataDict) -> AuthResult:
    return {"success": False}


def blocksmith_list_snippets(context: Context, data_dict: DataDict) -> AuthResult:
    return {"success": False}


def blocksmith_delete_snippet(context: Context, data_dict: DataDict) -> AuthResult:
    return {"success": False}


@tk.auth_allow_anonymous_access
def blocksmith_get_snippet(context: Context, data_dict: DataDict) -> AuthResult:
    snippet_id = tk.get_or_bust(data_dict, "id")

    snippet = model.SnippetModel.get_by_id(snippet_id)

    if not snippet:
        return {"success": False}

    if not tk.current_user.is_anonymous and tk.current_user.sysadmin:
        return {"success": True}

    return {"success": False}


@tk.auth_allow_anonymous_access
def blocksmith_get_page(context: Context, data_dict: DataDict) -> AuthResult:
    page_id = tk.get_or_bust(data_dict, "id")

    page = model.PageModel.get_by_id(page_id)

    if page and page.published:
        return {"success": True}

    if not tk.current_user.is_anonymous and tk.current_user.sysadmin:
        return {"success": True}

    return {"success": False}


def blocksmith_manage_menu(context: Context, data_dict: DataDict) -> AuthResult:
    return {"success": False}
