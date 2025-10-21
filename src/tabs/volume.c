#ifdef VOLUME_TAB
#define _GNU_SOURCE

#include "tabs/volume.h"

#include <gtk/gtk.h>
#include <pipewire/extensions/metadata.h>
#include <pipewire/pipewire.h>

#include "ui.h"


struct VolumeData
{
    struct
    {
        GtkScale *input;
        GtkScale *output;
    } scale;

    struct
    {
        GtkBox *input;
        GtkBox *output;
    } app_list;

    struct
    {
        struct pw_main_loop *loop;
        struct pw_context   *context;
        struct pw_core      *core;
        struct pw_registry  *registry;

        struct spa_hook registry_listener;

        struct
        {
            guint32 sink;
            guint32 source;
        } default_device_id;

        /* struct AppInfo * */
        GList *app_list;

        /* struct DeviceInfo * */
        GList *sink_device_list;
        GList *source_device_list;
    } pw;

    float volume;
    bool  done;
};

struct AppInfo
{
    guint32 client_id;
    guint32 stream_id;

    gchar app_name[256];
    gchar media_class[256];
    gchar icon_path[PATH_MAX];
};


typedef enum : guint8
{
    AUDIO_SINK   = 0,
    AUDIO_SOURCE = 1,
    AUDIO_NONE   = 2
} AudioType;

struct DeviceInfo
{
    AudioType type;

    char   *name;
    guint32 id;
};


static void
registry_global(void *data, guint32 id, guint32 perms, const char *type,
                guint32 version, const struct spa_dict *props)
{
    struct VolumeData *d = data;

    if (g_str_equal(type, PW_TYPE_INTERFACE_Client)) {}
    if (g_str_equal(type, PW_TYPE_INTERFACE_Metadata)) {}
    if (g_str_equal(type, PW_TYPE_INTERFACE_Node))
    {
        const char *media_class = spa_dict_lookup(props, PW_KEY_MEDIA_CLASS);
        const char *name        = spa_dict_lookup(props, PW_KEY_NODE_NAME);

        if (media_class == nullptr) return;
        AudioType type = AUDIO_NONE;

        if (g_str_equal(media_class, "Audio/Sink"))
            type = AUDIO_SINK;
        else if (g_str_equal(media_class, "Audio/Source"))
            type = AUDIO_SOURCE;

        if (type == AUDIO_NONE) return;

        struct DeviceInfo *dev = g_new(struct DeviceInfo, 1);
        if (dev == nullptr) exit(errno);

        dev->type = type;
        dev->name = g_strdup(name);
        dev->id   = id;

        GList *list = type == AUDIO_SINK ? d->pw.sink_device_list
                                         : d->pw.source_device_list;

        list = g_list_append(list, dev);
    }
}


static void
registry_event_global_remove(void *data, guint32 id)
{
    struct VolumeData *d = data;

    GList **current_list = &d->pw.sink_device_list;
    GList  *list         = *current_list;

    while (list != nullptr)
    {
        struct DeviceInfo *device = list->data;

        if (device->id == id)
        {
            *current_list = g_list_remove(*current_list, device);

            g_free(device->name);
            g_free(device);
            return;
        }
        list = list->next;
    }

    current_list = &d->pw.source_device_list;
    list         = *current_list;

    while (list != nullptr)
    {
        struct DeviceInfo *device = list->data;

        if (device->id == id)
        {
            *current_list = g_list_remove(*current_list, device);

            g_free(device->name);
            g_free(device);
            return;
        }
        list = list->next;
    }
}


static const struct pw_registry_events REGISTRY_EVENTS
    = { PW_VERSION_REGISTRY_EVENTS, .global = registry_global,
        .global_remove = registry_event_global_remove };


void
volume_tab_new(struct TabWidget *tab_data)
{
    struct VolumeData *data = g_new(struct VolumeData, 1);
    tab_data->destructor    = volume_tab_delete;

    data->pw.sink_device_list   = g_list_alloc();
    data->pw.source_device_list = g_list_alloc();
    data->pw.app_list           = g_list_alloc();

    pw_init(nullptr, nullptr);
    data->pw.loop = pw_main_loop_new(nullptr);
    data->pw.context
        = pw_context_new(pw_main_loop_get_loop(data->pw.loop), nullptr, 0);
    data->pw.core = pw_context_connect(data->pw.context, nullptr, 0);
    data->pw.registry
        = pw_core_get_registry(data->pw.core, PW_VERSION_REGISTRY, 0);

    spa_zero(data->pw.registry_listener);
    pw_registry_add_listener(data->pw.registry, &data->pw.registry_listener,
                             &REGISTRY_EVENTS, data);

    pw_main_loop_run(data->pw.loop);

    tab_data->data = data;
}


static void
print_data(gpointer data, gpointer user_data)
{
    struct DeviceInfo *dev = data;
    g_print("%hhu: %s %u\n", dev->type, dev->name, dev->id);
}


void
volume_tab_delete(struct TabWidget *tab_data)
{
    struct VolumeData *data = tab_data->data;

    pw_proxy_destroy((struct pw_proxy *)data->pw.registry);
    pw_core_disconnect(data->pw.core);
    pw_context_destroy(data->pw.context);
    pw_main_loop_destroy(data->pw.loop);
    pw_deinit();

    g_list_foreach(data->pw.sink_device_list, print_data, nullptr);

    g_list_free_full(data->pw.sink_device_list, g_free);
    g_list_free_full(data->pw.source_device_list, g_free);
    g_list_free_full(data->pw.app_list, g_free);

    g_free(data);
}


#endif
