#include <gtk/gtk.h>

#include "volume.h"
#include "wifi.h"

static void activate(GtkApplication *app, gpointer user_data) {
	GtkBuilder *builder = gtk_builder_new_from_file("ui.glade");
	GtkWidget *window =
	    GTK_WIDGET(gtk_builder_get_object(builder, "main_window"));

	GtkCssProvider *provider = gtk_css_provider_new();
	gtk_css_provider_load_from_path(provider, "style.css", NULL);
	gtk_style_context_add_provider_for_screen(
	    gdk_screen_get_default(), GTK_STYLE_PROVIDER(provider),
	    GTK_STYLE_PROVIDER_PRIORITY_USER);
	g_object_unref(provider);

	GtkWidget *wifi_box =
	    GTK_WIDGET(gtk_builder_get_object(builder, "wifi_box"));
	build_wifi_tab(wifi_box);

	GtkWidget *volume_box =
	    GTK_WIDGET(gtk_builder_get_object(builder, "volume_box"));
	build_volume_tab(volume_box);

	gtk_window_set_application(GTK_WINDOW(window), app);
	gtk_widget_show_all(window);
	g_object_unref(builder);
}

int main(int argc, char **argv) {
	GtkApplication *app =
	    gtk_application_new("org.bc.com", G_APPLICATION_DEFAULT_FLAGS);
	g_signal_connect(app, "activate", G_CALLBACK(activate), NULL);
	int status = g_application_run(G_APPLICATION(app), argc, argv);
	g_object_unref(app);
	return status;
}

