#include <dirent.h>
#include <glib.h>
#include <gtk/gtk.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

static GtkWidget *autostart_list;

typedef struct {
	gchar *system_path;
	GtkSwitch *sw;
} AutoEntryData;

static void toggle_autostart(AutoEntryData *entry, gboolean state) {
	if (!entry || !entry->system_path) return;

	gchar *user_dir =
	    g_build_filename(g_get_home_dir(), ".config", "autostart", NULL);
	g_mkdir_with_parents(user_dir, 0755);
	gchar *user_path = g_build_filename(
	    user_dir, g_path_get_basename(entry->system_path), NULL);
	g_free(user_dir);

	gchar *content = NULL;
	if (g_file_get_contents(entry->system_path, &content, NULL, NULL)) {
		gchar **lines = g_strsplit(content, "\n", 0);
		gboolean has_hidden = FALSE;

		for (int i = 0; lines[i]; i++) {
			if (g_str_has_prefix(lines[i], "Hidden=")) {
				g_free(lines[i]);
				lines[i] = g_strdup(state ? "Hidden=false"
							  : "Hidden=true");
				has_hidden = TRUE;
			}
		}

		if (!has_hidden) {
			int len = 0;
			while (lines[len]) len++;
			lines = g_realloc(lines, sizeof(gchar *) * (len + 2));
			lines[len] =
			    g_strdup(state ? "Hidden=false" : "Hidden=true");
			lines[len + 1] = NULL;
		}

		gchar *new_content = g_strjoinv("\n", lines);
		g_file_set_contents(user_path, new_content, -1, NULL);
		g_strfreev(lines);
		g_free(new_content);
		g_free(content);
	}

	g_free(user_path);
}

static void switch_cb(GtkSwitch *sw, gboolean state, gpointer user_data) {
	AutoEntryData *data = user_data;
	toggle_autostart(data, state);
}

static void populate_autostart_row(const gchar *name, const gchar *system_path,
				   gboolean enabled) {
	GtkWidget *row = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 8);
	gtk_widget_set_name(row, "network_row");

	GtkWidget *label = gtk_label_new(name);
	gtk_label_set_xalign(GTK_LABEL(label), 0.0);

	GtkWidget *sw = gtk_switch_new();
	gtk_switch_set_active(GTK_SWITCH(sw), enabled);

	AutoEntryData *data = g_malloc(sizeof(AutoEntryData));
	data->system_path = g_strdup(system_path);
	data->sw = GTK_SWITCH(sw);

	g_signal_connect(sw, "state-set", G_CALLBACK(switch_cb), data);

	gtk_box_pack_start(GTK_BOX(row), label, TRUE, TRUE, 6);
	gtk_box_pack_start(GTK_BOX(row), sw, FALSE, FALSE, 6);
	gtk_box_pack_start(GTK_BOX(autostart_list), row, FALSE, TRUE, 0);

	gtk_widget_show_all(row);
}

static gboolean load_autostart_entries(gpointer user_data) {
	gtk_container_foreach(GTK_CONTAINER(autostart_list),
			      (GtkCallback)gtk_widget_destroy, NULL);

	const char *dirs[] = {"/etc/xdg/autostart"};

	for (int d = 0; d < 1; d++) {
		DIR *dir = opendir(dirs[d]);
		if (!dir) continue;

		struct dirent *entry;
		while ((entry = readdir(dir)) != NULL) {
			if (!g_str_has_suffix(entry->d_name, ".desktop"))
				continue;

			gchar *system_path =
			    g_build_filename(dirs[d], entry->d_name, NULL);
			struct stat st;
			if (stat(system_path, &st) != 0 ||
			    !S_ISREG(st.st_mode)) {
				g_free(system_path);
				continue;
			}

			gchar *user_path =
			    g_build_filename(g_get_home_dir(), ".config",
					     "autostart", entry->d_name, NULL);

			gchar *content = NULL;
			gboolean enabled = TRUE;
			if (g_file_test(user_path, G_FILE_TEST_EXISTS))
				g_file_get_contents(user_path, &content, NULL,
						    NULL);
			else
				g_file_get_contents(system_path, &content, NULL,
						    NULL);

			if (content && strstr(content, "Hidden=true"))
				enabled = FALSE;

			gchar *name = g_strdup(entry->d_name);
			if (content) {
				gchar **lines = g_strsplit(content, "\n", 0);
				for (int i = 0; lines[i]; i++) {
					if (g_str_has_prefix(lines[i],
							     "Name=")) {
						g_free(name);
						name = g_strdup(lines[i] + 5);
						break;
					}
				}
				g_strfreev(lines);
				g_free(content);
			}

			populate_autostart_row(name, system_path, enabled);
			g_free(name);
			g_free(system_path);
			g_free(user_path);
		}
		closedir(dir);
	}
	return TRUE;
}

void build_autostart_tab(GtkWidget *autostart_box) {
	gtk_container_foreach(GTK_CONTAINER(autostart_box),
			      (GtkCallback)gtk_widget_destroy, NULL);

	gtk_widget_set_name(autostart_box, "tab_box");

	GtkWidget *scroll = gtk_scrolled_window_new(NULL, NULL);
	gtk_scrolled_window_set_policy(GTK_SCROLLED_WINDOW(scroll),
				       GTK_POLICY_AUTOMATIC,
				       GTK_POLICY_AUTOMATIC);
	gtk_widget_set_hexpand(scroll, TRUE);
	gtk_widget_set_vexpand(scroll, TRUE);
	gtk_box_pack_start(GTK_BOX(autostart_box), scroll, TRUE, TRUE, 0);

	GtkWidget *content = gtk_box_new(GTK_ORIENTATION_VERTICAL, 12);
	gtk_container_add(GTK_CONTAINER(scroll), content);

	GtkWidget *header = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 12);
	gtk_widget_set_name(header, "tab_header");

	GtkWidget *icon =
	    gtk_image_new_from_icon_name("system-run", GTK_ICON_SIZE_DIALOG);
	GtkWidget *label = gtk_label_new("Autostart Applications");
	gtk_label_set_xalign(GTK_LABEL(label), 0.0);

	GtkWidget *label_box = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 0);
	gtk_box_pack_start(GTK_BOX(label_box), label, TRUE, TRUE, 0);
	gtk_box_pack_start(GTK_BOX(header), icon, FALSE, FALSE, 0);
	gtk_box_pack_start(GTK_BOX(header), label_box, TRUE, TRUE, 0);
	gtk_box_pack_start(GTK_BOX(content), header, FALSE, TRUE, 8);

	GtkWidget *autostart_frame = gtk_frame_new("Autostart Applications");
	gtk_style_context_add_class(
	    gtk_widget_get_style_context(autostart_frame), "frame-title-bold");

	autostart_list = gtk_box_new(GTK_ORIENTATION_VERTICAL, 6);
	gtk_widget_set_margin_top(autostart_list, 12);
	gtk_widget_set_margin_bottom(autostart_list, 12);
	gtk_widget_set_margin_start(autostart_list, 12);
	gtk_widget_set_margin_end(autostart_list, 12);

	gtk_container_add(GTK_CONTAINER(autostart_frame), autostart_list);
	gtk_box_pack_start(GTK_BOX(content), autostart_frame, FALSE, TRUE, 8);

	load_autostart_entries(NULL);
	g_timeout_add_seconds(1, load_autostart_entries, NULL);
}

