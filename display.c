#include <glib.h>
#include <gtk/gtk.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>

static GtkWidget *brightness_slider;
static GtkWidget *bluelight_slider;
static GtkWidget *brightness_error_label;
static GtkWidget *bluelight_error_label;

static gchar *get_config_path(void) {
	const gchar *home = g_get_home_dir();
	gchar *dir = g_strdup_printf("%s/.cache/better-control", home);
	g_mkdir_with_parents(dir, 0755);  // ensure dir exists
	gchar *file = g_strdup_printf("%s/display.cfg", dir);
	g_free(dir);
	return file;
}

static void save_display_settings(int brightness, int bluelight) {
	gchar *path = get_config_path();
	FILE *f = fopen(path, "w");
	if (!f) {
		g_free(path);
		return;
	}
	fprintf(f, "%d %d\n", brightness, bluelight);
	fclose(f);
	g_free(path);
}

static void load_display_settings(int *brightness, int *bluelight) {
	gchar *path = get_config_path();
	FILE *f = fopen(path, "r");
	if (!f) {
		g_free(path);
		return;
	}
	fscanf(f, "%d %d", brightness, bluelight);
	fclose(f);
	g_free(path);
}

static gboolean command_exists(const char *cmd) {
	gchar *check_cmd =
	    g_strdup_printf("command -v %s >/dev/null 2>&1", cmd);
	int ret = system(check_cmd);
	g_free(check_cmd);
	return ret == 0;
}

static void brightness_changed(GtkRange *range, gpointer user_data) {
	double val = gtk_range_get_value(range);
	int nearest = ((int)(val + 5) / 10) * 10;  // nearest ticck
	if (fabs(val - nearest) <= 1) gtk_range_set_value(range, nearest);

	if (!command_exists("brightnessctl")) return;
	gchar *cmd = g_strdup_printf("brightnessctl set %d%%", (int)val);
	system(cmd);
	g_free(cmd);

	int brightness = (int)gtk_range_get_value(GTK_RANGE(brightness_slider));
	int bluelight = (int)gtk_range_get_value(GTK_RANGE(bluelight_slider));
	save_display_settings(brightness, bluelight);
}

static void bluelight_changed(GtkRange *range, gpointer user_data) {
	double val = gtk_range_get_value(range);
	int percentage = (int)val;
	int temperature = 2500 + (percentage * 40);

	if (!command_exists("gammastep")) return;

	system("pkill -f gammastep");

	gchar *cmd =
	    g_strdup_printf("gammastep -O %d >/dev/null 2>&1 &", temperature);
	system(cmd);
	g_free(cmd);

	int brightness = (int)gtk_range_get_value(GTK_RANGE(brightness_slider));
	int bluelight = (int)gtk_range_get_value(GTK_RANGE(bluelight_slider));
	save_display_settings(brightness, bluelight);
}

static void add_ticks(GtkScale *scale) {
	for (int i = 0; i <= 100; i += 10)
		gtk_scale_add_mark(scale, i, GTK_POS_BOTTOM,
				   g_strdup_printf("%d", i));
}

void build_display_tab(GtkWidget *display_box) {
	gtk_container_foreach(GTK_CONTAINER(display_box),
			      (GtkCallback)gtk_widget_destroy, NULL);
	gtk_widget_set_name(display_box, "tab_box");

	GtkWidget *scroll = gtk_scrolled_window_new(NULL, NULL);
	gtk_scrolled_window_set_policy(GTK_SCROLLED_WINDOW(scroll),
				       GTK_POLICY_AUTOMATIC,
				       GTK_POLICY_AUTOMATIC);
	gtk_widget_set_hexpand(scroll, TRUE);
	gtk_widget_set_vexpand(scroll, TRUE);
	gtk_box_pack_start(GTK_BOX(display_box), scroll, TRUE, TRUE, 0);

	GtkWidget *content = gtk_box_new(GTK_ORIENTATION_VERTICAL, 12);
	gtk_container_add(GTK_CONTAINER(scroll), content);

	GtkWidget *header = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 12);
	gtk_widget_set_name(header, "tab_header");
	GtkWidget *icon = gtk_image_new_from_icon_name(
	    "preferences-desktop-display", GTK_ICON_SIZE_DIALOG);
	GtkWidget *label = gtk_label_new("Display Settings");
	gtk_label_set_xalign(GTK_LABEL(label), 0.0);
	GtkWidget *label_box = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 0);
	gtk_box_pack_start(GTK_BOX(label_box), label, TRUE, TRUE, 0);
	gtk_box_pack_start(GTK_BOX(header), icon, FALSE, FALSE, 0);
	gtk_box_pack_start(GTK_BOX(header), label_box, TRUE, TRUE, 0);
	gtk_widget_show_all(header);
	gtk_box_pack_start(GTK_BOX(content), header, FALSE, TRUE, 8);

	GtkWidget *bright_frame = gtk_frame_new("Screen Brightness");
	gtk_style_context_add_class(gtk_widget_get_style_context(bright_frame),
				    "frame-title-bold");

	GtkWidget *bright_box = gtk_box_new(GTK_ORIENTATION_VERTICAL, 6);
	gtk_widget_set_margin_top(bright_box, 12);
	gtk_widget_set_margin_bottom(bright_box, 12);
	gtk_widget_set_margin_start(bright_box, 12);
	gtk_widget_set_margin_end(bright_box, 12);
	gtk_container_add(GTK_CONTAINER(bright_frame), bright_box);

	int saved_brightness = 50, saved_bluelight = 50;
	load_display_settings(&saved_brightness, &saved_bluelight);

	brightness_slider =
	    gtk_scale_new_with_range(GTK_ORIENTATION_HORIZONTAL, 0, 100, 10);
	gtk_scale_set_draw_value(GTK_SCALE(brightness_slider), TRUE);
	gtk_scale_set_digits(GTK_SCALE(brightness_slider), 0);
	add_ticks(GTK_SCALE(brightness_slider));
	gtk_range_set_value(GTK_RANGE(brightness_slider), saved_brightness);
	g_signal_connect(brightness_slider, "value-changed",
			 G_CALLBACK(brightness_changed), NULL);
	gtk_box_pack_start(GTK_BOX(bright_box), brightness_slider, FALSE, FALSE,
			   0);

	brightness_error_label = gtk_label_new("brightnessctl not found");
	gtk_label_set_xalign(GTK_LABEL(brightness_error_label), 0.0);
	gtk_widget_set_name(brightness_error_label, "error_label");
	if (command_exists("brightnessctl")) {
		gtk_widget_destroy(brightness_error_label);
	} else {
		gtk_box_pack_start(GTK_BOX(bright_box), brightness_error_label,
				   FALSE, FALSE, 6);
	}

	gtk_widget_show_all(bright_frame);
	gtk_box_pack_start(GTK_BOX(content), bright_frame, FALSE, TRUE, 8);

	GtkWidget *bluelight_frame = gtk_frame_new("Blue Light Filter");
	gtk_style_context_add_class(
	    gtk_widget_get_style_context(bluelight_frame), "frame-title-bold");

	GtkWidget *bluelight_box = gtk_box_new(GTK_ORIENTATION_VERTICAL, 6);
	gtk_widget_set_margin_top(bluelight_box, 12);
	gtk_widget_set_margin_bottom(bluelight_box, 12);
	gtk_widget_set_margin_start(bluelight_box, 12);
	gtk_widget_set_margin_end(bluelight_box, 12);
	gtk_container_add(GTK_CONTAINER(bluelight_frame), bluelight_box);

	bluelight_slider =
	    gtk_scale_new_with_range(GTK_ORIENTATION_HORIZONTAL, 0, 100, 10);
	gtk_scale_set_draw_value(GTK_SCALE(bluelight_slider), TRUE);
	gtk_scale_set_digits(GTK_SCALE(bluelight_slider), 0);
	add_ticks(GTK_SCALE(bluelight_slider));
	gtk_range_set_value(GTK_RANGE(bluelight_slider), saved_bluelight);
	g_signal_connect(bluelight_slider, "value-changed",
			 G_CALLBACK(bluelight_changed), NULL);
	gtk_box_pack_start(GTK_BOX(bluelight_box), bluelight_slider, FALSE,
			   FALSE, 0);

	if (!command_exists("gammastep")) {
		bluelight_error_label = gtk_label_new("gammastep not found");
		gtk_label_set_xalign(GTK_LABEL(bluelight_error_label), 0.0);
		gtk_widget_set_name(bluelight_error_label, "error_label");
		gtk_box_pack_start(GTK_BOX(bluelight_box),
				   bluelight_error_label, FALSE, FALSE, 6);
	}

	gtk_widget_show_all(bluelight_frame);
	gtk_box_pack_start(GTK_BOX(content), bluelight_frame, FALSE, TRUE, 8);
}

