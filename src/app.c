#include "app.h"

#include <gtk/gtk.h>

#include "ui.h"


static void
load_css()
{
    GtkCssProvider *provider = gtk_css_provider_new();
    gtk_css_provider_load_from_resource(provider, APP_PREFIX "/style.css");
    gtk_style_context_add_provider_for_screen(gdk_screen_get_default(),
                                              GTK_STYLE_PROVIDER(provider),
                                              GTK_STYLE_PROVIDER_PRIORITY_USER);
    g_object_unref(provider);
}


static void
create_tab(GHashTable *tabs, GtkBuilder *builder, const char *resource_path,
           const char *name)
{
    struct TabWidget *tab = g_new(struct TabWidget, 1);
    tab->box  = GTK_BOX(gtk_builder_get_object(builder, resource_path));
    tab->data = nullptr;

    g_hash_table_insert(tabs, (void *)g_strdup(name), tab);
}

#define CREATE_TAB(tab, builder, resource_path) \
    create_tab((tab), (builder), APP_PREFIX resource_path, (resource_path))


void
app_on_activate(GtkApplication *app, struct AppData *data)
{
    load_css();

    GtkBuilder *builder
        = gtk_builder_new_from_resource(APP_PREFIX "/window.glade");

    struct Widgets *widgets = g_new(struct Widgets, 1);
    widgets->tabs
        = g_hash_table_new_full(g_str_hash, g_str_equal, g_free, g_free);

    widgets->window
        = GTK_WINDOW(gtk_builder_get_object(builder, "main_window"));

    gtk_window_set_application(widgets->window, app);


    CREATE_TAB(widgets->tabs, builder, "autostart");
    CREATE_TAB(widgets->tabs, builder, "display");
    CREATE_TAB(widgets->tabs, builder, "network");
    CREATE_TAB(widgets->tabs, builder, "volume");
    g_object_unref(builder);

    data->widgets = widgets;
    gtk_widget_show_all(GTK_WIDGET(data->widgets->window));
}


void
app_on_shutdown(GtkApplication *, struct AppData *data)
{
    g_hash_table_destroy(data->widgets->tabs);
    g_free(data->widgets);
    g_free(data->args);
}
