#include <gtk/gtk.h>

#include "app.h"


void *
create_args(int argc, char **argv)
{
    void *args     = g_malloc(sizeof(int) + (argc * sizeof(char *)));
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

