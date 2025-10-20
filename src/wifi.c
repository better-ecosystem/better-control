#include <curl/curl.h>
#include <glib.h>
#include <gtk/gtk.h>
#include <stdlib.h>
#include <string.h>

static GtkWidget *speed_label;
static GtkWidget *download_label_global;
static GtkWidget *upload_label_global;
static GtkWidget *networks_list;
static gchar *active_ssid = NULL;

static GtkWidget *conn_info_label;

static gboolean public_ip_visible = FALSE;
static GtkWidget *public_ip_label = NULL;
static gchar public_ip[64] = "***.**.**.***";

typedef struct {
	GtkLabel *label;
	GtkButton *button;
} EyeData;

static void update_connection_info(void);
static void toggle_public_ip(GtkButton *button, gpointer user_data) {
	public_ip_visible = !public_ip_visible;
	update_connection_info();

	// update icon
	EyeData *data = user_data;
	GtkImage *img = GTK_IMAGE(gtk_button_get_image(data->button));
	gtk_image_set_from_icon_name(img,
				     public_ip_visible
					 ? "view-reveal-symbolic"
					 : "view-conceal-symbolic",
				     GTK_ICON_SIZE_BUTTON);
}

static size_t curl_write_cb(void *ptr, size_t size, size_t nmemb,
			    void *stream) {
	strncat((char *)stream, (char *)ptr, size * nmemb);
	return size * nmemb;
}

static void update_connection_info() {
	gchar priv_ip[64] = "", gateway[64] = "", dns[128] = "";
	gchar *out = NULL;

	g_spawn_command_line_sync(
	    "nmcli -t -f IP4.ADDRESS,IP4.GATEWAY,IP4.DNS dev show", &out, NULL,
	    NULL, NULL);
	if (out) {
		gchar **lines = g_strsplit(out, "\n", 0);
		for (int i = 0; lines[i]; i++) {
			gchar *line = g_strstrip(lines[i]);
			if (g_str_has_prefix(line, "IP4.ADDRESS") &&
			    priv_ip[0] == '\0') {
				gchar **parts = g_strsplit(line, ":", 2);
				if (parts[1]) {
					gchar *ip = g_strstrip(parts[1]);
					if (strncmp(ip, "127.", 4) != 0)
						strncpy(priv_ip, ip,
							sizeof(priv_ip));
				}
				g_strfreev(parts);
			} else if (g_str_has_prefix(line, "IP4.GATEWAY") &&
				   gateway[0] == '\0') {
				gchar **parts = g_strsplit(line, ":", 2);
				if (parts[1]) {
					gchar *gw = g_strstrip(parts[1]);
					if (strlen(gw) > 0)
						strncpy(gateway, gw,
							sizeof(gateway));
				}
				g_strfreev(parts);
			} else if (g_str_has_prefix(line, "IP4.DNS")) {
				gchar **parts = g_strsplit(line, ":", 2);
				if (parts[1]) {
					strncat(dns, g_strstrip(parts[1]),
						sizeof(dns) - strlen(dns) - 1);
					strncat(dns, " ",
						sizeof(dns) - strlen(dns) - 1);
				}
				g_strfreev(parts);
			}
		}
		g_strfreev(lines);
		g_free(out);
	}

	CURL *curl = curl_easy_init();
	if (curl) {
		char buffer[64] = "";
		curl_easy_setopt(curl, CURLOPT_URL, "https://api.ipify.org");
		curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, curl_write_cb);
		curl_easy_setopt(curl, CURLOPT_WRITEDATA, buffer);
		curl_easy_setopt(curl, CURLOPT_TIMEOUT, 2L);
		curl_easy_perform(curl);
		curl_easy_cleanup(curl);
		strncpy(public_ip, buffer, sizeof(public_ip));
	}

	gchar combined[512];
	snprintf(combined, sizeof(combined),
		 "Private: %s  •  DNS: %s  •  Gateway: %s  •  Public: %s",
		 priv_ip, gateway, dns,
		 public_ip_visible ? public_ip : "***.**.**.***");

	gtk_label_set_text(GTK_LABEL(conn_info_label), combined);
}

typedef struct {
	const char *cmd;
	void (*callback)(gchar *);
} CmdTaskData;

typedef struct {
	void (*callback)(gchar *);
	gchar *output;
} IdleData;

static gboolean idle_callback(gpointer data) {
	IdleData *d = (IdleData *)data;
	if (d->callback) d->callback(d->output);
	g_free(d->output);
	g_free(d);
	return FALSE;
}

static gpointer run_command_thread(gpointer data) {
	CmdTaskData *task = (CmdTaskData *)data;
	gchar *out = NULL;  // fix that
	gchar *err = NULL;  // and this
	gint status;
	g_spawn_command_line_sync(task->cmd, &out, &err, &status, NULL);
	gchar *full_output = err && strlen(err) > 0 ? g_strdup(err)
			     : out		    ? g_strdup(out)
						    : g_strdup("");
	IdleData *idle = g_malloc(sizeof(IdleData));
	idle->callback = task->callback;
	idle->output = full_output;
	g_idle_add(idle_callback, idle);
	g_free(out);
	g_free(err);
	g_free(task);
	return NULL;
}

static void run_command_async(const char *cmd, void (*callback)(gchar *)) {
	CmdTaskData *task = g_malloc(sizeof(CmdTaskData));
	task->cmd = cmd;
	task->callback = callback;
	GThread *thread = g_thread_new(NULL, run_command_thread, task);
	g_thread_unref(thread);
}

static void show_popup(GtkWindow *parent, const char *title, const char *msg,
		       GtkMessageType type) {
	GtkWidget *dialog = gtk_message_dialog_new(
	    parent, GTK_DIALOG_MODAL | GTK_DIALOG_DESTROY_WITH_PARENT, type,
	    GTK_BUTTONS_OK, "%s", msg);
	gtk_window_set_title(GTK_WINDOW(dialog), title);
	gtk_window_set_keep_above(GTK_WINDOW(dialog), TRUE);
	GtkWidget *content = gtk_bin_get_child(GTK_BIN(dialog));
	gtk_widget_set_margin_top(content, 12);
	gtk_widget_set_margin_bottom(content, 12);
	gtk_widget_set_margin_start(content, 12);
	gtk_widget_set_margin_end(content, 12);
	gtk_dialog_run(GTK_DIALOG(dialog));
	gtk_widget_destroy(dialog);
}

static void show_wrong_password_popup() {
	show_popup(NULL, "Connection Failed",
		   "Wrong password or authentication failed!",
		   GTK_MESSAGE_ERROR);
}

static void connect_check_cb(gchar *out) {
	if (out && (strstr(out, "Error") || strstr(out, "secrets") ||
		    strstr(out, "failed")))
		show_wrong_password_popup();
}

static void connect_button_clicked(GtkWidget *button, gpointer user_data) {
	gchar **userdata = (gchar **)user_data;
	gchar *ssid = userdata[0];
	gchar *security = userdata[1];
	gboolean is_connected = GPOINTER_TO_INT(userdata[2]);

	if (is_connected) {
		gchar cmd[256];
		snprintf(cmd, sizeof(cmd), "nmcli con down id '%s'", ssid);
		run_command_async(cmd, NULL);
	} else {
		GtkWidget *dialog = gtk_dialog_new_with_buttons(
		    "Connect to Wi-Fi", NULL,
		    GTK_DIALOG_MODAL | GTK_DIALOG_DESTROY_WITH_PARENT,
		    "_Connect", GTK_RESPONSE_OK, "_Cancel", GTK_RESPONSE_CANCEL,
		    NULL);
		gtk_window_set_keep_above(GTK_WINDOW(dialog), TRUE);

		GtkWidget *content_area =
		    gtk_dialog_get_content_area(GTK_DIALOG(dialog));
		gtk_widget_set_margin_top(content_area, 12);
		gtk_widget_set_margin_bottom(content_area, 12);
		gtk_widget_set_margin_start(content_area, 12);
		gtk_widget_set_margin_end(content_area, 12);

		GtkWidget *label = gtk_label_new(
		    "Enter password (leave blank for open network):");
		gtk_box_pack_start(GTK_BOX(content_area), label, FALSE, FALSE,
				   6);

		GtkWidget *entry_pass = gtk_entry_new();
		gtk_entry_set_visibility(GTK_ENTRY(entry_pass), FALSE);
		gtk_box_pack_start(GTK_BOX(content_area), entry_pass, FALSE,
				   FALSE, 6);

		GtkWidget *entry_user = NULL;
		if (security && strstr(security, "EAP")) {
			GtkWidget *label_user =
			    gtk_label_new("Enter username:");
			gtk_box_pack_start(GTK_BOX(content_area), label_user,
					   FALSE, FALSE, 6);
			entry_user = gtk_entry_new();
			gtk_box_pack_start(GTK_BOX(content_area), entry_user,
					   FALSE, FALSE, 6);
		}

		GtkWidget *combo_sec = gtk_combo_box_text_new();
		if (security && strlen(security) > 0) {
			gchar **secs = g_strsplit(security, " ", 0);
			for (int i = 0; secs[i]; i++)
				gtk_combo_box_text_append_text(
				    GTK_COMBO_BOX_TEXT(combo_sec), secs[i]);
			gtk_combo_box_set_active(GTK_COMBO_BOX(combo_sec), 0);
			g_strfreev(secs);
		} else {
			gtk_combo_box_text_append_text(
			    GTK_COMBO_BOX_TEXT(combo_sec), "Open");
			gtk_combo_box_set_active(GTK_COMBO_BOX(combo_sec), 0);
		}
		gtk_box_pack_start(GTK_BOX(content_area), combo_sec, FALSE,
				   FALSE, 6);

		gtk_widget_show_all(dialog);

		if (gtk_dialog_run(GTK_DIALOG(dialog)) == GTK_RESPONSE_OK) {
			const gchar *password =
			    gtk_entry_get_text(GTK_ENTRY(entry_pass));
			const gchar *username =
			    entry_user
				? gtk_entry_get_text(GTK_ENTRY(entry_user))
				: NULL;
			const gchar *selected_sec =
			    gtk_combo_box_text_get_active_text(
				GTK_COMBO_BOX_TEXT(combo_sec));
			gchar cmd[512];

			if (selected_sec && g_strrstr(selected_sec, "WPA3"))
				snprintf(cmd, sizeof(cmd),
					 "nmcli dev wifi connect '%s' password "
					 "'%s' wifi-sec.key-mgmt sae",
					 ssid, password ? password : "");
			else if (selected_sec &&
				 (g_strrstr(selected_sec, "WPA2") ||
				  g_strrstr(selected_sec, "WPA1 WPA2")))
				snprintf(cmd, sizeof(cmd),
					 "nmcli dev wifi connect '%s' password "
					 "'%s' wifi-sec.key-mgmt wpa-psk",
					 ssid, password ? password : "");
			else if (selected_sec && g_strrstr(selected_sec, "WEP"))
				snprintf(
				    cmd, sizeof(cmd),
				    "nmcli dev wifi connect '%s' wep-key0 '%s'",
				    ssid, password ? password : "");
			else if (selected_sec && g_strrstr(selected_sec, "EAP"))
				snprintf(cmd, sizeof(cmd),
					 "nmcli dev wifi connect '%s' password "
					 "'%s' identity '%s'",
					 ssid, password ? password : "",
					 username ? username : "");
			else
				snprintf(cmd, sizeof(cmd),
					 "nmcli dev wifi connect '%s'", ssid);

			run_command_async(cmd, connect_check_cb);
		}

		gtk_widget_destroy(dialog);
	}

	g_free(ssid);
	g_free(security);
	g_free(userdata);
}

static void populate_networks_row(const gchar *ssid, const gchar *signal,
				  const gchar *bars, const gchar *security,
				  gboolean is_active) {
	GtkWidget *row = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 8);
	gtk_widget_set_name(row, "rows");
	if (is_active)
		gtk_style_context_add_class(gtk_widget_get_style_context(row),
					    "active_network");

	GtkWidget *icon = gtk_image_new_from_icon_name(
	    "network-wireless", GTK_ICON_SIZE_SMALL_TOOLBAR);
	GtkWidget *label = gtk_label_new(ssid);
	gtk_label_set_xalign(GTK_LABEL(label), 0.0);

	gchar buf[32];
	snprintf(buf, sizeof(buf), "%s%% %s", signal, bars);
	GtkWidget *signal_label = gtk_label_new(buf);
	gtk_label_set_xalign(GTK_LABEL(signal_label), 1.0);

	GtkWidget *btn = gtk_button_new();
	gtk_button_set_label(GTK_BUTTON(btn),
			     is_active ? "Disconnect" : "Connect");

	gchar **userdata = g_malloc(sizeof(gchar *) * 3);
	userdata[0] = g_strdup(ssid);
	userdata[1] = g_strdup(security ? security : "");
	userdata[2] = GINT_TO_POINTER(is_active);
	g_signal_connect(btn, "clicked", G_CALLBACK(connect_button_clicked),
			 userdata);

	gtk_box_pack_start(GTK_BOX(row), icon, FALSE, FALSE, 6);
	gtk_box_pack_start(GTK_BOX(row), label, TRUE, TRUE, 6);
	gtk_box_pack_start(GTK_BOX(row), signal_label, FALSE, FALSE, 6);
	gtk_box_pack_start(GTK_BOX(row), btn, FALSE, FALSE, 6);

	if (is_active)
		gtk_box_pack_start(GTK_BOX(networks_list), row, FALSE, TRUE, 0);
	else
		gtk_box_pack_end(GTK_BOX(networks_list), row, FALSE, TRUE, 0);

	gtk_widget_show_all(row);
}

static gchar *active_iface = NULL;
static unsigned long long prev_rx = 0, prev_tx = 0;

// find better way later cuz kei said unsafe but works for now!

static void update_speed_cb(gchar *out) {
	if (!out) return;

	gchar **lines = g_strsplit(out, "\n", 0);
	for (int i = 0; lines[i]; i++) {
		if (lines[i][0] == '*') {
			gchar **fields = g_strsplit(lines[i], ":", 0);
			if (fields[1]) {
				int signal = atoi(fields[2]);
				double speed = signal * 0.7;
				char buf[128];
				snprintf(buf, sizeof(buf),
					 "Connection speed: %.1f Mbps (signal: "
					 "%d%%)",
					 speed, signal);
				gtk_label_set_text(GTK_LABEL(speed_label), buf);

				if (!active_iface) {
					gchar *iface_out = NULL;
					g_spawn_command_line_sync(
					    "nmcli -t -f DEVICE,TYPE,STATE dev",
					    &iface_out, NULL, NULL, NULL);
					if (iface_out) {
						gchar **devlines = g_strsplit(
						    iface_out, "\n", 0);
						for (int j = 0; devlines[j];
						     j++) {
							gchar **devfields =
							    g_strsplit(
								devlines[j],
								":", 0);
							if (devfields[1] &&
							    strcmp(devfields[1],
								   "wifi") ==
								0 &&
							    devfields[2] &&
							    strcmp(
								devfields[2],
								"connected") ==
								0) {
								active_iface =
								    g_strdup(
									devfields
									    [0]);
								break;
							}
							g_strfreev(devfields);
						}
						g_strfreev(devlines);
						g_free(iface_out);
					}
				}

				if (active_iface) {
					FILE *f = fopen("/proc/net/dev", "r");
					if (f) {
						char line[512];
						unsigned long long rx = 0,
								   tx = 0;
						while (fgets(line, sizeof(line),
							     f)) {
							char iface[32];
							unsigned long long r, t;
							int matched = sscanf(
							    line,
							    " %31[^:]: %llu "
							    "%*u %*u %*u %*u "
							    "%*u %*u %*u %llu",
							    iface, &r, &t);
							if (matched == 3 &&
							    strcmp(
								iface,
								active_iface) ==
								0) {
								rx = r;
								tx = t;
								break;
							}
						}
						fclose(f);

						double download_mbps = 0,
						       upload_mbps = 0;
						if (prev_rx && prev_tx) {
							download_mbps =
							    (double)(rx -
								     prev_rx) *
							    8 / 1000000.0;
							upload_mbps =
							    (double)(tx -
								     prev_tx) *
							    8 / 1000000.0;
						}
						prev_rx = rx;
						prev_tx = tx;

						snprintf(buf, sizeof(buf),
							 "Downloads: %.2f Mbps",
							 download_mbps);
						gtk_label_set_text(
						    GTK_LABEL(
							download_label_global),
						    buf);
						snprintf(buf, sizeof(buf),
							 "Uploads: %.2f Mbps",
							 upload_mbps);
						gtk_label_set_text(
						    GTK_LABEL(
							upload_label_global),
						    buf);
					}
				}
			}
			g_strfreev(fields);
			break;
		}
	}
	g_strfreev(lines);
}

static void scan_networks_cb(gchar *out) {
	gtk_container_foreach(GTK_CONTAINER(networks_list),
			      (GtkCallback)gtk_widget_destroy, NULL);
	if (!out || strlen(out) == 0) {
		GtkWidget *loading_label =
		    gtk_label_new("   No networks found.");
		gtk_label_set_xalign(GTK_LABEL(loading_label), 0.0);
		gtk_box_pack_start(GTK_BOX(networks_list), loading_label, FALSE,
				   FALSE, 6);
		gtk_widget_show_all(loading_label);
		return;
	}
	gchar **lines = g_strsplit(out, "\n", 0);
	for (int i = 0; lines[i]; i++) {
		if (strlen(lines[i]) == 0) continue;
		gboolean is_active = (lines[i][0] == '*');
		gchar **fields = g_strsplit(lines[i], ":", 0);
		if (fields[1]) {
			if (is_active) {
				if (active_ssid) g_free(active_ssid);
				active_ssid = g_strdup(fields[1]);
			}
			const gchar *ssid = fields[1];
			const gchar *signal = fields[2] ? fields[2] : "0";
			const gchar *bars = fields[3] ? fields[3] : "";
			const gchar *security = fields[4] ? fields[4] : "";
			populate_networks_row(ssid, signal, bars, security,
					      is_active);
		}
		g_strfreev(fields);
	}
	g_strfreev(lines);
}

static gboolean speed_timer_cb(gpointer user_data) {
	run_command_async("nmcli -t -f IN-USE,SSID,SIGNAL dev wifi",
			  update_speed_cb);
	return TRUE;
}

static gboolean scan_timer_cb(gpointer user_data) {
	run_command_async(
	    "nmcli -t -f IN-USE,SSID,SIGNAL,BARS,SECURITY dev wifi",
	    scan_networks_cb);
	return TRUE;
}

static gboolean wifi_toggle_cb(GtkSwitch *sw, gboolean state,
			       gpointer user_data) {
	const char *cmd =
	    state ? "nmcli radio wifi on" : "nmcli radio wifi off";
	run_command_async(cmd, NULL);
	return FALSE;
}
void build_wifi_tab(GtkWidget *wifi_box) {
	gtk_container_foreach(GTK_CONTAINER(wifi_box),
			      (GtkCallback)gtk_widget_destroy, NULL);
	gtk_widget_set_name(wifi_box, "tab_box");

	GtkWidget *scroll = gtk_scrolled_window_new(NULL, NULL);
	gtk_scrolled_window_set_policy(GTK_SCROLLED_WINDOW(scroll),
				       GTK_POLICY_AUTOMATIC,
				       GTK_POLICY_AUTOMATIC);
	gtk_widget_set_hexpand(scroll, TRUE);
	gtk_widget_set_vexpand(scroll, TRUE);
	gtk_box_pack_start(GTK_BOX(wifi_box), scroll, TRUE, TRUE, 0);

	GtkWidget *content = gtk_box_new(GTK_ORIENTATION_VERTICAL, 12);
	gtk_container_add(GTK_CONTAINER(scroll), content);

	GtkWidget *header = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 12);
	gtk_widget_set_name(header, "tab_header");

	GtkWidget *icon = gtk_image_new_from_icon_name("network-wireless",
						       GTK_ICON_SIZE_DIALOG);

	GtkWidget *label = gtk_label_new("Wi-Fi Networks");
	gtk_label_set_xalign(GTK_LABEL(label), 0.0);

	GtkWidget *label_box = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 0);
	gtk_box_pack_start(GTK_BOX(label_box), label, TRUE, TRUE, 0);

	GtkWidget *wifi_toggle = gtk_switch_new();
	gtk_widget_set_halign(wifi_toggle, GTK_ALIGN_END);
	gtk_widget_set_valign(wifi_toggle, GTK_ALIGN_CENTER);

	gtk_box_pack_start(GTK_BOX(header), icon, FALSE, FALSE, 0);
	gtk_box_pack_start(GTK_BOX(header), label_box, TRUE, TRUE, 0);
	gtk_box_pack_start(GTK_BOX(header), wifi_toggle, FALSE, FALSE, 0);

	gchar *out = NULL;
	g_spawn_command_line_sync("nmcli radio wifi", &out, NULL, NULL, NULL);
	if (out && strstr(out, "enabled"))
		gtk_switch_set_active(GTK_SWITCH(wifi_toggle), TRUE);
	else
		gtk_switch_set_active(GTK_SWITCH(wifi_toggle), FALSE);
	g_free(out);

	g_signal_connect(wifi_toggle, "state-set", G_CALLBACK(wifi_toggle_cb),
			 NULL);

	gtk_box_pack_start(GTK_BOX(header), icon, FALSE, FALSE, 0);
	gtk_box_pack_start(GTK_BOX(header), label, TRUE, TRUE, 0);
	gtk_box_pack_start(GTK_BOX(header), wifi_toggle, FALSE, FALSE, 0);

	gtk_widget_show_all(header);
	gtk_box_pack_start(GTK_BOX(content), header, FALSE, TRUE, 8);

	GtkWidget *speed_frame = gtk_frame_new("Connection Info");
	gtk_style_context_add_class(gtk_widget_get_style_context(speed_frame),
				    "frame-title-bold");

	GtkWidget *speed_box = gtk_box_new(GTK_ORIENTATION_VERTICAL, 6);
	gtk_widget_set_margin_top(speed_box, 12);
	gtk_widget_set_margin_bottom(speed_box, 12);
	gtk_widget_set_margin_start(speed_box, 12);
	gtk_widget_set_margin_end(speed_box, 12);
	gtk_container_add(GTK_CONTAINER(speed_frame), speed_box);

	speed_label = gtk_label_new("Connection Speed : Calculating...");
	gtk_label_set_xalign(GTK_LABEL(speed_label), 0.0);
	gtk_box_pack_start(GTK_BOX(speed_box), speed_label, FALSE, FALSE, 0);

	download_label_global = gtk_label_new("Downloads: Calculating...");
	gtk_label_set_xalign(GTK_LABEL(download_label_global), 0.0);
	gtk_box_pack_start(GTK_BOX(speed_box), download_label_global, FALSE,
			   FALSE, 0);

	upload_label_global = gtk_label_new("Uploads: Calculating...");
	gtk_label_set_xalign(GTK_LABEL(upload_label_global), 0.0);
	gtk_box_pack_start(GTK_BOX(speed_box), upload_label_global, FALSE,
			   FALSE, 0);

	GtkWidget *ip_box = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 6);
	gtk_box_pack_start(GTK_BOX(speed_box), ip_box, FALSE, FALSE, 0);

	conn_info_label = gtk_label_new("Calculating...");
	gtk_label_set_xalign(GTK_LABEL(conn_info_label), 0.0);
	gtk_box_pack_start(GTK_BOX(ip_box), conn_info_label, TRUE, TRUE, 0);

	GtkWidget *eye_btn = gtk_button_new_from_icon_name(
	    "view-conceal-symbolic", GTK_ICON_SIZE_BUTTON);

	EyeData *eye_data = g_malloc(sizeof(EyeData));
	eye_data->label =
	    GTK_LABEL(conn_info_label); 
	eye_data->button = GTK_BUTTON(eye_btn);

	g_signal_connect(eye_btn, "clicked", G_CALLBACK(toggle_public_ip),
			 eye_data);

	gtk_box_pack_start(GTK_BOX(ip_box), eye_btn, FALSE, FALSE, 0);

	gtk_box_pack_start(GTK_BOX(speed_box), ip_box, FALSE, FALSE, 0);

	gtk_widget_show_all(speed_frame);
	gtk_box_pack_start(GTK_BOX(content), speed_frame, FALSE, TRUE, 8);

	GtkWidget *networks_frame = gtk_frame_new("Available Networks");
	gtk_style_context_add_class(
	    gtk_widget_get_style_context(networks_frame), "frame-title-bold");

	networks_list = gtk_box_new(GTK_ORIENTATION_VERTICAL, 6);

	GtkWidget *loading_label = gtk_label_new("   Loading networks...");
	gtk_label_set_xalign(GTK_LABEL(loading_label), 0.0);
	gtk_box_pack_start(GTK_BOX(networks_list), loading_label, FALSE, FALSE,
			   6);
	gtk_widget_show_all(loading_label);

	gtk_container_add(GTK_CONTAINER(networks_frame), networks_list);
	gtk_widget_show_all(networks_frame);
	gtk_box_pack_start(GTK_BOX(content), networks_frame, FALSE, TRUE, 8);

	g_timeout_add_seconds(2, speed_timer_cb, NULL);
	g_timeout_add_seconds(5, scan_timer_cb, NULL);
	g_timeout_add_seconds(2, (GSourceFunc)update_connection_info, NULL);
}

