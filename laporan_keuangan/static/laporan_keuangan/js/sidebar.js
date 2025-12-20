// ---------- SIDEBAR ----------
function toggleSidebar() {
    const sidebar = document.getElementById("sidebar");
    sidebar.classList.toggle("collapsed");

    localStorage.setItem(
        "sidebar-collapsed",
        sidebar.classList.contains("collapsed")
    );

    // If collapsing sidebar, hide all menu items
    if (sidebar.classList.contains("collapsed")) {
        document.querySelectorAll(".menu-items").forEach(m => {
            m.style.display = "none";
        });
        localStorage.setItem("open-menus", JSON.stringify([]));
    }
}

// ---------- MENU GROUP ----------
function toggleGroup(menuId) {
    const sidebar = document.getElementById("sidebar");
    const menu = document.getElementById(menuId);

    // If sidebar is collapsed, expand it first
    if (sidebar.classList.contains("collapsed")) {
        sidebar.classList.remove("collapsed");
        localStorage.setItem("sidebar-collapsed", false);
    }

    const isOpen = menu.style.display === "block";

    menu.style.display = isOpen ? "none" : "block";

    saveOpenMenus();
}

// ---------- STATE PERSISTENCE ----------
function saveOpenMenus() {
    const openMenus = [];
    document.querySelectorAll(".menu-items").forEach(menu => {
        if (menu.style.display === "block") {
            openMenus.push(menu.id);
        }
    });
    localStorage.setItem("open-menus", JSON.stringify(openMenus));
}

function restoreSidebarState() {
    const sidebar = document.getElementById("sidebar");
    const collapsed = localStorage.getItem("sidebar-collapsed") === "true";

    if (collapsed) {
        sidebar.classList.add("collapsed");
    }

    const openMenus = JSON.parse(localStorage.getItem("open-menus") || "[]");
    openMenus.forEach(id => {
        const menu = document.getElementById(id);
        if (menu) menu.style.display = "block";
    });
}

// ---------- INIT ----------
document.addEventListener("DOMContentLoaded", restoreSidebarState);
