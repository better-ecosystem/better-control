#include <gtk/gtk.h>

#include "autostart.h"
#include "display.h"
#include "volume.h"
#include "wifi.h"
#include "app.h"


static void
on_activate(GtkApplication *app, gpointer user_data)
{
    GtkBuilder *builder
        = gtk_builder_new_from_resource(APP_PREFIX "window.glade");
    GtkWidget *window
        = GTK_WIDGET(gtk_builder_get_object(builder, "main_window"));

    GtkCssProvider *provider = gtk_css_provider_new();
    gtk_css_provider_load_from_path(provider, "style.css", nullptr);
    gtk_style_context_add_provider_for_screen(gdk_screen_get_default(),
                                              GTK_STYLE_PROVIDER(provider),
                                              GTK_STYLE_PROVIDER_PRIORITY_USER);
    g_object_unref(provider);

    GtkWidget *wifi_box
        = GTK_WIDGET(gtk_builder_get_object(builder, "wifi_box"));
    build_wifi_tab(wifi_box);

    GtkWidget *volume_box
        = GTK_WIDGET(gtk_builder_get_object(builder, "volume_box"));
    build_volume_tab(volume_box);

    GtkWidget *display_box
        = GTK_WIDGET(gtk_builder_get_object(builder, "display_box"));
    build_display_tab(display_box);

    GtkWidget *autostart_box
        = GTK_WIDGET(gtk_builder_get_object(builder, "autostart_box"));
    build_autostart_tab(autostart_box);


    gtk_window_set_application(GTK_WINDOW(window), app);
    gtk_widget_show_all(window);
    g_object_unref(builder);
}


void *
create_args(int argc, char **argv)
{
    void *args = g_malloc(sizeof(int) + (argc * sizeof(char *)));
    (*(int *)args) = argc;

    char **strings = (char **)((char *)args + sizeof(int));
    memcpy((void *)strings, (void *)argv, argc * sizeof(char *));
    return args;
}


int
main(int argc, char **argv)
{
    GtkApplication *app
        = gtk_application_new(APP_ID, G_APPLICATION_DEFAULT_FLAGS);

    struct AppData data;

    data.args = create_args(argc, argv);

    g_signal_connect(app, "activate", G_CALLBACK(app_on_activate), &data);
    g_signal_connect(app, "shutdown", G_CALLBACK(app_on_shutdown), &data);
    int status = g_application_run(G_APPLICATION(app), 0, nullptr);

    g_object_unref(app);
    return status;
}

