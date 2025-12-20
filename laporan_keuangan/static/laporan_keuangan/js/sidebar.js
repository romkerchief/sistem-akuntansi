/**
 * Sidebar Navigation Controller
 * Handles sidebar toggle, menu expansion, and state persistence
 */
(function () {
    'use strict';

    const STORAGE_KEYS = {
        collapsed: 'sidebar-collapsed',
        openMenus: 'open-menus'
    };

    const sidebar = () => document.getElementById('sidebar');

    // ---------- Sidebar Toggle ----------
    window.toggleSidebar = function () {
        const el = sidebar();
        if (!el) return;

        el.classList.toggle('collapsed');
        const isCollapsed = el.classList.contains('collapsed');

        localStorage.setItem(STORAGE_KEYS.collapsed, isCollapsed);

        // Close all menus when collapsing
        if (isCollapsed) {
            closeAllMenus();
            localStorage.setItem(STORAGE_KEYS.openMenus, '[]');
        }
    };

    // ---------- Menu Group Toggle ----------
    window.toggleGroup = function (menuId) {
        const el = sidebar();
        const menu = document.getElementById(menuId);
        if (!el || !menu) return;

        // Expand sidebar if collapsed
        if (el.classList.contains('collapsed')) {
            el.classList.remove('collapsed');
            localStorage.setItem(STORAGE_KEYS.collapsed, false);
        }

        // Toggle menu visibility
        const isOpen = menu.style.display === 'block';
        menu.style.display = isOpen ? 'none' : 'block';

        // Toggle arrow rotation on parent title
        const title = menu.previousElementSibling;
        if (title) {
            title.classList.toggle('open', !isOpen);
        }

        saveOpenMenus();
    };

    // ---------- Helper Functions ----------
    function closeAllMenus() {
        document.querySelectorAll('.menu-items').forEach(menu => {
            menu.style.display = 'none';
        });
        document.querySelectorAll('.menu-title').forEach(title => {
            title.classList.remove('open');
        });
    }

    function saveOpenMenus() {
        const openMenus = [];
        document.querySelectorAll('.menu-items').forEach(menu => {
            if (menu.style.display === 'block' && menu.id) {
                openMenus.push(menu.id);
            }
        });
        localStorage.setItem(STORAGE_KEYS.openMenus, JSON.stringify(openMenus));
    }

    function restoreState() {
        const el = sidebar();
        if (!el) return;

        // Restore collapsed state
        const isCollapsed = localStorage.getItem(STORAGE_KEYS.collapsed) === 'true';
        el.classList.toggle('collapsed', isCollapsed);

        // Restore open menus (only if not collapsed)
        if (!isCollapsed) {
            try {
                const openMenus = JSON.parse(localStorage.getItem(STORAGE_KEYS.openMenus) || '[]');
                openMenus.forEach(id => {
                    const menu = document.getElementById(id);
                    if (menu) {
                        menu.style.display = 'block';
                        const title = menu.previousElementSibling;
                        if (title) title.classList.add('open');
                    }
                });
            } catch (e) {
                // Reset if invalid JSON
                localStorage.setItem(STORAGE_KEYS.openMenus, '[]');
            }
        }
    }

    // ---------- Initialize ----------
    document.addEventListener('DOMContentLoaded', restoreState);
})();
