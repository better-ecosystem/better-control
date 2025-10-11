#include <gtk/gtk.h>

void build_volume_tab(GtkWidget *volume_box) {
	gtk_container_foreach(GTK_CONTAINER(volume_box),
			      (GtkCallback)gtk_widget_destroy, NULL);
	gtk_widget_set_name(volume_box, "tab_box");

	GtkWidget *header = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 12);
	gtk_widget_set_name(header, "tab_header");
	GtkWidget *icon =
	    gtk_image_new_from_icon_name("audio-card", GTK_ICON_SIZE_DIALOG);
	GtkWidget *label = gtk_label_new("Volume Control");
	gtk_label_set_xalign(GTK_LABEL(label), 0.0);

	gtk_box_pack_start(GTK_BOX(header), icon, FALSE, FALSE, 0);
	gtk_box_pack_start(GTK_BOX(header), label, TRUE, TRUE, 0);
	gtk_box_pack_start(GTK_BOX(volume_box), header, FALSE, TRUE, 8);

	GtkWidget *nested_notebook = gtk_notebook_new();
	gtk_notebook_set_tab_pos(GTK_NOTEBOOK(nested_notebook), GTK_POS_TOP);
	gtk_box_pack_start(GTK_BOX(volume_box), nested_notebook, TRUE, TRUE, 0);

	GtkWidget *placeholder = gtk_label_new("Volume tab placeholder");
	gtk_box_pack_start(GTK_BOX(volume_box), placeholder, TRUE, TRUE, 0);

	gtk_widget_show_all(volume_box);
}

