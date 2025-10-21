#ifdef VOLUME_TAB
#define _GNU_SOURCE

#include "tabs/volume.h"

#include <gtk/gtk.h>
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
        struct spa_hook      registry_listener;

        guint32 target_node_id;
        gchar   target_name[128];
        bool    found;
    } pw;
};


static void
registry_global(void *data, uint32_t id, uint32_t, const char *type, uint32_t,
                const struct spa_dict *props)
{
    struct VolumeData *d = data;

    const char *media_class = spa_dict_lookup(props, "media.class");
    const char *node_name   = spa_dict_lookup(props, PW_KEY_NODE_NAME);

    if (strcmp(type, PW_TYPE_INTERFACE_Node) == 0 && media_class && node_name)
    {
        if (strcmp(node_name, d->pw.target_name) == 0)
        {
            d->pw.target_node_id = id;
            d->pw.found          = true;
        }
    }
}

static const struct pw_registry_events REGISTRY_EVENTS = {
    PW_VERSION_REGISTRY_EVENTS,
    .global = registry_global,
};


void
volume_tab_create(struct TabWidget *tab_data)
{
    struct VolumeData *data = g_new(struct VolumeData, 1);
    tab_data->destructor    = volume_tab_delete;

    pw_init(nullptr, nullptr);
}


void
volume_tab_delete(struct TabWidget *tab_data)
{
    pw_deinit();
}


#endif
