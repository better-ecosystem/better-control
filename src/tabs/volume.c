#include "tabs/volume.h"

#include <gtk/gtk.h>

#include "tabs/volume_logic.h"
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

    struct VolumeLogicContext *ctx;

    float volume;

    /* struct ClientInfo * */
    GList *client_list;

    /* struct DeviceInfo * */
    GHashTable *device_list[2];
};


struct ClientInfo
{
    guint32 client_id;
    guint32 stream_id;

    gchar app_name[256];
    gchar media_class[256];
    gchar icon_path[PATH_MAX];
};

struct DeviceInfo
{
    char *name;
    float volume;
};


static void
device_info_delete(void *dev)
{
    g_free(((struct DeviceInfo *)dev)->name);
    g_free(dev);
}


static void
on_device_added(VolumeType type, guint32 id, const char *name, gpointer data)
{
    struct VolumeData *d = data;

    GHashTable        *table = d->device_list[type];
    struct DeviceInfo *dev   = g_new(struct DeviceInfo, 1);

    dev->name   = g_strdup(name);
    dev->volume = 0.0F;

    g_hash_table_insert(table, GUINT_TO_POINTER(id), dev);
}


static void
on_device_remove(guint32 id, gpointer data)
{
    struct VolumeData *d = data;
    struct DeviceInfo *dev;

    for (VolumeType type = 0; type < 2; type++)
    {
        if (g_hash_table_contains(d->device_list[type], GUINT_TO_POINTER(id)))
        {
            dev = g_hash_table_lookup(d->device_list[type],
                                      GUINT_TO_POINTER(id));
            g_hash_table_remove(d->device_list[type], GUINT_TO_POINTER(id));

            g_free(dev->name);
            g_free(dev);
            return;
        }
    }
}


static const struct VolumeLogicInterface VOLUME_INTERFACE = {
    .on_device_added  = on_device_added,
    .on_device_remove = on_device_remove,
};


void
volume_tab_new(struct TabWidget *tab_data)
{
    struct VolumeData *data = g_new(struct VolumeData, 1);
    tab_data->destructor    = volume_tab_delete;

    data->device_list[0] = g_hash_table_new_full(g_direct_hash, g_direct_equal,
                                                 nullptr, device_info_delete);
    data->device_list[1] = g_hash_table_new_full(g_direct_hash, g_direct_equal,
                                                 nullptr, device_info_delete);

    data->client_list = nullptr;

    volume_logic_init(&data->ctx);
    volume_logic_add_interface(data->ctx, &VOLUME_INTERFACE, data);

    tab_data->data = data;
}


void
volume_tab_delete(struct TabWidget *tab_data)
{
    struct VolumeData *data = tab_data->data;

    volume_logic_deinit(data->ctx);

    g_hash_table_destroy(data->device_list[0]);
    g_hash_table_destroy(data->device_list[1]);
    g_list_free_full(data->client_list, g_free);

    g_free(data);
}
