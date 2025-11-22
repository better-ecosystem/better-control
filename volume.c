#include "volume.h"

#include <glib.h>
#include <gtk/gtk.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>

static GtkWidget *speaker_slider;
static GtkWidget *mic_slider;
static GtkWidget *app_output_box;
static GtkWidget *app_input_box;

static gchar *get_config_path(void) {
	const gchar *home = g_get_home_dir();
	gchar *dir = g_strdup_printf("%s/.cache/better-control", home);
	g_mkdir_with_parents(dir, 0755);
	gchar *file = g_strdup_printf("%s/volume.cfg", dir);
	g_free(dir);
	return file;
}

static void save_volume_settings(int speaker, int mic) {
	gchar *path = get_config_path();
	FILE *f = fopen(path, "w");
	if (!f) {
		g_free(path);
		return;
	}
	fprintf(f, "%d %d\n", speaker, mic);
	fclose(f);
	g_free(path);
}

static void load_volume_settings(int *speaker, int *mic) {
	gchar *path = get_config_path();
	FILE *f = fopen(path, "r");
	if (!f) {
		g_free(path);
		return;
	}
	fscanf(f, "%d %d", speaker, mic);
	fclose(f);
	g_free(path);
}

static void set_system_volume(int percent) {
	gchar *cmd = g_strdup_printf(
	    "pactl set-sink-volume @DEFAULT_SINK@ %d%%", percent);
	system(cmd);
	g_free(cmd);
}

static void set_mic_volume(int percent) {
	gchar *cmd = g_strdup_printf(
	    "pactl set-source-volume @DEFAULT_SOURCE@ %d%%", percent);
	system(cmd);
	g_free(cmd);
}

static void add_volume_ticks(GtkScale *scale) {
	for (int i = 0; i <= 100; i += 10)
		gtk_scale_add_mark(scale, i, GTK_POS_BOTTOM,
				   g_strdup_printf("%d", i));
}

static void slider_changed_cb(GtkRange *range, gpointer user_data) {
	double val = gtk_range_get_value(range);
	int nearest = ((int)(val + 5) / 10) * 10;  // SNAAAP
	if (fabs(val - nearest) <= 1) {
		gtk_range_set_value(range, nearest);
		val = nearest;
	}

	const gchar *type = user_data;
	int value = (int)val;

	if (g_strcmp0(type, "speaker") == 0)
		set_system_volume(value);
	else if (g_strcmp0(type, "mic") == 0)
		set_mic_volume(value);

	int speaker = (int)gtk_range_get_value(GTK_RANGE(speaker_slider));
	int mic = (int)gtk_range_get_value(GTK_RANGE(mic_slider));
	save_volume_settings(speaker, mic);
}

static void set_app_volume(GtkRange *range, gpointer user_data) {
	int encoded = GPOINTER_TO_INT(user_data);
	int index = encoded >> 1;
	gboolean is_input = encoded & 1;

	double val = gtk_range_get_value(range);
	int nearest = ((int)(val + 5) / 10) * 10;
	if (fabs(val - nearest) <= 1) {
		gtk_range_set_value(range, nearest);
		val = nearest;
	}

	int volume = (int)val;
	const gchar *target = is_input ? "source-output" : "sink-input";
	gchar *cmd = g_strdup_printf("pactl set-%s-volume %d %d%%", target,
				     index, volume);
	system(cmd);
	g_free(cmd);
}

static void rebuild_app_list(GtkWidget *box, gboolean is_input) {
	gtk_container_foreach(GTK_CONTAINER(box),
			      (GtkCallback)gtk_widget_destroy, NULL);

	const char *list_type = is_input ? "source-outputs" : "sink-inputs";
	gchar *cmd = g_strdup_printf("pactl list %s", list_type);
	FILE *fp = popen(cmd, "r");
	if (!fp) {
		g_free(cmd);
		return;
	}

	char line[1024];
	int index = -1;
	char app_name[256] = "Unknown";
	int volume = -1;

	while (fgets(line, sizeof(line), fp)) {
		line[strcspn(line, "\n")] = 0;

		if (g_str_has_prefix(line, "Sink Input #") ||
		    g_str_has_prefix(line, "Source Output #")) {
			if (index != -1 && volume >= 0) {
				GtkWidget *row =
				    gtk_box_new(GTK_ORIENTATION_VERTICAL, 2);
				gtk_widget_set_name(row, "rows");

				GtkWidget *label = gtk_label_new(app_name);
				gtk_label_set_xalign(GTK_LABEL(label), 0.0);
				gtk_widget_set_hexpand(label, FALSE);
				gtk_widget_set_halign(label, GTK_ALIGN_START);

				GtkWidget *slider = gtk_scale_new_with_range(
				    GTK_ORIENTATION_HORIZONTAL, 0, 100, 10);
				gtk_scale_set_draw_value(GTK_SCALE(slider),
							 TRUE);
				gtk_scale_set_digits(GTK_SCALE(slider), 0);
				add_volume_ticks(GTK_SCALE(slider));
				gtk_range_set_value(GTK_RANGE(slider), volume);
				gtk_widget_set_hexpand(slider, TRUE);

				gpointer user_data = GINT_TO_POINTER(
				    (index << 1) | (is_input ? 1 : 0));
				g_signal_connect(slider, "value-changed",
						 G_CALLBACK(set_app_volume),
						 user_data);

				gtk_box_pack_start(GTK_BOX(row), label, FALSE,
						   FALSE, 4);
				gtk_box_pack_start(GTK_BOX(row), slider, TRUE,
						   TRUE, 4);
				gtk_box_pack_start(GTK_BOX(box), row, FALSE,
						   FALSE, 2);
				gtk_widget_show_all(row);
			}

			if (sscanf(line, "Sink Input #%d", &index) == 1 ||
			    sscanf(line, "Source Output #%d", &index) == 1) {
				strcpy(app_name, "Unknown");
				volume = -1;
			} else {
				index = -1;
			}
		} else if (strstr(line, "application.name = ")) {
			char *eq = strchr(line, '=');
			if (eq) {
				char *start = eq + 1;
				while (*start == ' ' || *start == '\t') start++;
				if (*start == '"') {
					start++;
					char *end = strchr(start, '"');
					if (end) {
						int len = end - start;
						if (len > 0 &&
						    len <
							(int)sizeof(app_name) -
							    1) {
							strncpy(app_name, start,
								len);
							app_name[len] = '\0';
						}
					}
				}
			}
		} else if (strstr(line, "Volume:")) {
			char *perc = strstr(line, "%");
			if (perc) {
				char *num_start = perc - 1;
				while (num_start > line &&
				       g_ascii_isdigit(*(num_start - 1))) {
					num_start--;
				}
				if (num_start > line) {
					volume = atoi(num_start);
				}
			}
		} else if (strstr(line, "media.name = ")) {
			char *eq = strchr(line, '=');
			if (eq) {
				char *start = eq + 1;
				while (*start == ' ' || *start == '\t') start++;
				if (*start == '"') {
					start++;
					char *end = strchr(start, '"');
					if (end) {
						int len = end - start;
						if (len > 0 &&
						    len <
							(int)sizeof(app_name) -
							    1) {
							strncpy(app_name, start,
								len);
							app_name[len] = '\0';
						}
					}
				}
			}
		}
	}

	if (index != -1 && volume >= 0) {
		GtkWidget *row = gtk_box_new(GTK_ORIENTATION_VERTICAL, 2);
		gtk_widget_set_name(row, "rows");

		GtkWidget *label = gtk_label_new(app_name);
		gtk_label_set_xalign(GTK_LABEL(label), 0.0);
		gtk_widget_set_hexpand(label, FALSE);
		gtk_widget_set_halign(label, GTK_ALIGN_START);

		GtkWidget *slider = gtk_scale_new_with_range(
		    GTK_ORIENTATION_HORIZONTAL, 0, 100, 10);
		gtk_scale_set_draw_value(GTK_SCALE(slider), TRUE);
		gtk_scale_set_digits(GTK_SCALE(slider), 0);
		add_volume_ticks(GTK_SCALE(slider));
		gtk_range_set_value(GTK_RANGE(slider), volume);
		gtk_widget_set_hexpand(slider, TRUE);

		gpointer user_data =
		    GINT_TO_POINTER((index << 1) | (is_input ? 1 : 0));
		g_signal_connect(slider, "value-changed",
				 G_CALLBACK(set_app_volume), user_data);

		gtk_box_pack_start(GTK_BOX(row), label, FALSE, FALSE, 4);
		gtk_box_pack_start(GTK_BOX(row), slider, TRUE, TRUE, 4);
		gtk_box_pack_start(GTK_BOX(box), row, FALSE, FALSE, 2);
		gtk_widget_show_all(row);
	}

	pclose(fp);
	g_free(cmd);
}

static gboolean refresh_app_volumes(gpointer data) {
	rebuild_app_list(app_output_box, FALSE);
	rebuild_app_list(app_input_box, TRUE);
	return TRUE;
}

void build_volume_tab(GtkWidget *volume_box) {
	// why css twice fix later
	GtkCssProvider *provider = gtk_css_provider_new();
	GdkDisplay *display = gdk_display_get_default();
	GdkScreen *screen = gdk_display_get_default_screen(display);
	gtk_style_context_add_provider_for_screen(
	    screen, GTK_STYLE_PROVIDER(provider),
	    GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);
	gtk_css_provider_load_from_path(provider, "style.css", NULL);
	g_object_unref(provider);

	gtk_container_foreach(GTK_CONTAINER(volume_box),
			      (GtkCallback)gtk_widget_destroy, NULL);
	gtk_widget_set_name(volume_box, "tab_box");

	GtkWidget *scroll = gtk_scrolled_window_new(NULL, NULL);
	gtk_scrolled_window_set_policy(GTK_SCROLLED_WINDOW(scroll),
				       GTK_POLICY_AUTOMATIC,
				       GTK_POLICY_AUTOMATIC);
	gtk_widget_set_hexpand(scroll, TRUE);
	gtk_widget_set_vexpand(scroll, TRUE);
	gtk_box_pack_start(GTK_BOX(volume_box), scroll, TRUE, TRUE, 0);

	GtkWidget *content = gtk_box_new(GTK_ORIENTATION_VERTICAL, 12);
	gtk_container_add(GTK_CONTAINER(scroll), content);

	// DONT FORGET TITLE
	GtkWidget *header = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 12);
	gtk_widget_set_name(header, "tab_header");
	GtkWidget *icon = gtk_image_new_from_icon_name("audio-volume-high",
						       GTK_ICON_SIZE_DIALOG);
	GtkWidget *label = gtk_label_new("Volume Control");
	gtk_label_set_xalign(GTK_LABEL(label), 0.0);
	GtkWidget *label_box = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 0);
	gtk_box_pack_start(GTK_BOX(label_box), label, TRUE, TRUE, 0);
	gtk_box_pack_start(GTK_BOX(header), icon, FALSE, FALSE, 0);
	gtk_box_pack_start(GTK_BOX(header), label_box, TRUE, TRUE, 0);
	gtk_widget_show_all(header);
	gtk_box_pack_start(GTK_BOX(content), header, FALSE, TRUE, 8);

	// smaller tabs
	GtkWidget *notebook = gtk_notebook_new();
	gtk_box_pack_start(GTK_BOX(content), notebook, TRUE, TRUE, 0);

	int speaker = 50, mic = 50;
	load_volume_settings(&speaker, &mic);

	// speaker here
	GtkWidget *speaker_tab = gtk_box_new(GTK_ORIENTATION_VERTICAL, 8);
	gtk_widget_set_name(speaker_tab, "tab_content");

	GtkWidget *speaker_frame = gtk_frame_new("Speaker Volume");
	gtk_widget_set_name(speaker_frame, "frame");
	gtk_style_context_add_class(gtk_widget_get_style_context(speaker_frame),
				    "frame-title-bold");

	GtkWidget *speaker_box = gtk_box_new(GTK_ORIENTATION_VERTICAL, 6);
	gtk_widget_set_margin_top(speaker_box, 12);
	gtk_widget_set_margin_bottom(speaker_box, 12);
	gtk_widget_set_margin_start(speaker_box, 12);
	gtk_widget_set_margin_end(speaker_box, 12);
	gtk_container_add(GTK_CONTAINER(speaker_frame), speaker_box);

	speaker_slider =
	    gtk_scale_new_with_range(GTK_ORIENTATION_HORIZONTAL, 0, 100, 10);
	gtk_scale_set_draw_value(GTK_SCALE(speaker_slider), TRUE);
	gtk_scale_set_digits(GTK_SCALE(speaker_slider), 0);
	add_volume_ticks(GTK_SCALE(speaker_slider));
	gtk_range_set_value(GTK_RANGE(speaker_slider), speaker);
	g_signal_connect(speaker_slider, "value-changed",
			 G_CALLBACK(slider_changed_cb), "speaker");
	gtk_box_pack_start(GTK_BOX(speaker_box), speaker_slider, FALSE, FALSE,
			   0);

	gtk_widget_show_all(speaker_frame);
	gtk_box_pack_start(GTK_BOX(speaker_tab), speaker_frame, FALSE, TRUE, 8);

	gtk_notebook_append_page(GTK_NOTEBOOK(notebook), speaker_tab,
				 gtk_label_new("Speaker"));

	GtkWidget *mic_tab = gtk_box_new(GTK_ORIENTATION_VERTICAL, 8);
	gtk_widget_set_name(mic_tab, "tab_content");

	GtkWidget *mic_frame = gtk_frame_new("Microphone Volume");
	gtk_widget_set_name(mic_frame, "frame");
	gtk_style_context_add_class(gtk_widget_get_style_context(mic_frame),
				    "frame-title-bold");

	GtkWidget *mic_box = gtk_box_new(GTK_ORIENTATION_VERTICAL, 6);
	gtk_widget_set_margin_top(mic_box, 12);
	gtk_widget_set_margin_bottom(mic_box, 12);
	gtk_widget_set_margin_start(mic_box, 12);
	gtk_widget_set_margin_end(mic_box, 12);
	gtk_container_add(GTK_CONTAINER(mic_frame), mic_box);

	mic_slider =
	    gtk_scale_new_with_range(GTK_ORIENTATION_HORIZONTAL, 0, 100, 10);
	gtk_scale_set_draw_value(GTK_SCALE(mic_slider), TRUE);
	gtk_scale_set_digits(GTK_SCALE(mic_slider), 0);
	add_volume_ticks(GTK_SCALE(mic_slider));
	gtk_range_set_value(GTK_RANGE(mic_slider), mic);
	g_signal_connect(mic_slider, "value-changed",
			 G_CALLBACK(slider_changed_cb), "mic");
	gtk_box_pack_start(GTK_BOX(mic_box), mic_slider, FALSE, FALSE, 0);

	gtk_widget_show_all(mic_frame);
	gtk_box_pack_start(GTK_BOX(mic_tab), mic_frame, FALSE, TRUE, 8);

	gtk_notebook_append_page(GTK_NOTEBOOK(notebook), mic_tab,
				 gtk_label_new("Microphone"));

	GtkWidget *app_output_tab = gtk_box_new(GTK_ORIENTATION_VERTICAL, 8);
	gtk_widget_set_name(app_output_tab, "tab_content");

	GtkWidget *app_output_frame =
	    gtk_frame_new("Application Output Volumes");
	gtk_widget_set_name(app_output_frame, "frame");
	gtk_style_context_add_class(
	    gtk_widget_get_style_context(app_output_frame), "frame-title-bold");

	app_output_box = gtk_box_new(GTK_ORIENTATION_VERTICAL, 6);
	gtk_widget_set_margin_top(app_output_box, 12);
	gtk_widget_set_margin_bottom(app_output_box, 12);
	gtk_widget_set_margin_start(app_output_box, 12);
	gtk_widget_set_margin_end(app_output_box, 12);
	gtk_container_add(GTK_CONTAINER(app_output_frame), app_output_box);

	gtk_widget_show_all(app_output_frame);
	gtk_box_pack_start(GTK_BOX(app_output_tab), app_output_frame, TRUE,
			   TRUE, 8);

	gtk_notebook_append_page(GTK_NOTEBOOK(notebook), app_output_tab,
				 gtk_label_new("App Output"));

	GtkWidget *app_input_tab = gtk_box_new(GTK_ORIENTATION_VERTICAL, 8);
	gtk_widget_set_name(app_input_tab, "tab_content");

	GtkWidget *app_input_frame = gtk_frame_new("Application Input Volumes");
	gtk_widget_set_name(app_input_frame, "frame");
	gtk_style_context_add_class(
	    gtk_widget_get_style_context(app_input_frame), "frame-title-bold");

	app_input_box = gtk_box_new(GTK_ORIENTATION_VERTICAL, 6);
	gtk_widget_set_margin_top(app_input_box, 12);
	gtk_widget_set_margin_bottom(app_input_box, 12);
	gtk_widget_set_margin_start(app_input_box, 12);
	gtk_widget_set_margin_end(app_input_box, 12);
	gtk_container_add(GTK_CONTAINER(app_input_frame), app_input_box);

	gtk_widget_show_all(app_input_frame);
	gtk_box_pack_start(GTK_BOX(app_input_tab), app_input_frame, TRUE, TRUE,
			   8);

	gtk_notebook_append_page(GTK_NOTEBOOK(notebook), app_input_tab,
				 gtk_label_new("App Input"));

	gtk_widget_show_all(notebook);

	refresh_app_volumes(NULL);

	g_timeout_add_seconds(3, refresh_app_volumes, NULL);
}
