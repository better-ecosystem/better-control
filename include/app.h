#pragma once
#include <glib.h>

typedef struct _GtkApplication GtkApplication; // NOLINT


struct AppData
{
    struct Widgets *widgets;
    void *args;
};


void app_on_activate(GtkApplication *app, struct AppData *data);
void app_on_shutdown(GtkApplication *app, struct AppData *data);