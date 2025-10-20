#pragma once
#include <gtk/gtk.h>


struct TabWidget
{
    void   *data; /* a pointer containing each tab's buffer data */
    GtkBox *box;
};


struct Widgets
{
    GtkWindow *window;
    GHashTable *tabs; /* each tab contains a struct TabWidget * */
};
