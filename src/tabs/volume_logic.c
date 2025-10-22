#define _GNU_SOURCE

#include "tabs/volume_logic.h"

#include <pipewire/extensions/metadata.h>
#include <pipewire/pipewire.h>
#include <spa/param/param.h>
#include <spa/utils/result.h>


struct PipewireSource
{
    GSource         base;
    struct pw_loop *loop;
};

struct VolumeLogicContext
{
    GMainLoop             *main_loop;
    struct PipewireSource *source;
    struct pw_context     *context;
    struct pw_core        *core;
    struct pw_registry    *registry;

    struct spa_hook registry_listener;

    GPtrArray *interfaces;
    GPtrArray *interface_datas;
};


static gboolean
pipewire_loop_source_dispatch(GSource *source, GSourceFunc callback,
                              gpointer user_data)
{
    struct PipewireSource *s = (struct PipewireSource *)source;

    int result = pw_loop_iterate(s->loop, 0);
    if (result < 0)
        g_warning("pipewire_loop_iterate failed: %s", spa_strerror(result));

    return TRUE;
}

static GSourceFuncs pipewire_source_funcs = {
    .dispatch = pipewire_loop_source_dispatch,
};


static void
registry_global(gpointer data, guint32 id, guint32 perms, const char *type,
                guint32 version, const struct spa_dict *props)
{
    struct VolumeLogicContext *ctx = data;

    if (g_str_equal(type, PW_TYPE_INTERFACE_Client)) {}
    if (g_str_equal(type, PW_TYPE_INTERFACE_Metadata)) {}
    if (g_str_equal(type, PW_TYPE_INTERFACE_Node))
    {
        const char *media_class = spa_dict_lookup(props, PW_KEY_MEDIA_CLASS);
        const char *name        = spa_dict_lookup(props, PW_KEY_NODE_NAME);

        if (media_class == nullptr) return;

        int volume_type = -1;
        if (g_str_equal(media_class, "Audio/Sink"))
            volume_type = VOLUME_SINK;
        else if (g_str_equal(media_class, "Audio/Source"))
            volume_type = VOLUME_SOURCE;

        if (volume_type == -1) return;

        for (size_t i = 0; i < ctx->interfaces->len; i++)
        {
            struct VolumeLogicInterface *interface = ctx->interfaces->pdata[i];
            gpointer interface_data = ctx->interface_datas->pdata[i];

            if (interface->on_device_added)
                interface->on_device_added(volume_type, id, name,
                                           interface_data);
        }
    }
}


static void
registry_event_global_remove(gpointer data, guint32 id)
{
    struct VolumeLogicContext *ctx = data;

    for (size_t i = 0; i < ctx->interfaces->len; i++)
    {
        struct VolumeLogicInterface *interface = ctx->interfaces->pdata[i];
        gpointer interface_data                = ctx->interface_datas->pdata[i];

        if (interface->on_device_remove)
            interface->on_device_remove(id, interface_data);
    }
}


static const struct pw_registry_events REGISTRY_EVENTS
    = { PW_VERSION_REGISTRY_EVENTS, .global = registry_global,
        .global_remove = registry_event_global_remove };


static bool
volume_logic_init_pw(struct VolumeLogicContext **context)
{
    struct VolumeLogicContext *ctx = g_new(struct VolumeLogicContext, 1);
    const char                *err = nullptr;

    ctx->main_loop = g_main_loop_new(nullptr, FALSE);

    pw_init(nullptr, nullptr);

    ctx->source = (struct PipewireSource *)g_source_new(
        &pipewire_source_funcs, sizeof(struct PipewireSource));

    ctx->source->loop = pw_loop_new(nullptr);
    if (ctx->source->loop == nullptr)
    {
        g_main_loop_unref(ctx->main_loop);

        err = "pw_loop_new failed";
        goto __err;
    }

    g_source_add_unix_fd(&ctx->source->base, pw_loop_get_fd(ctx->source->loop),
                         G_IO_IN | G_IO_ERR);
    g_source_attach(&ctx->source->base, nullptr);
    g_source_unref(&ctx->source->base);

    ctx->context = pw_context_new(ctx->source->loop, nullptr, 0);
    if (ctx->context == nullptr)
    {
        pw_loop_destroy(ctx->source->loop);
        g_main_loop_unref(ctx->main_loop);

        err = "pw_context_new failed";
        goto __err;
    }

    ctx->core = pw_context_connect(ctx->context, nullptr, 0);
    if (ctx->core == nullptr)
    {
        pw_context_destroy(ctx->context);
        pw_loop_destroy(ctx->source->loop);
        g_main_loop_unref(ctx->main_loop);

        err = "pw_context_connect failed";
        goto __err;
    }

    ctx->registry = pw_core_get_registry(ctx->core, PW_VERSION_REGISTRY, 0);
    if (ctx->registry == nullptr)
    {
        pw_core_disconnect(ctx->core);
        pw_context_destroy(ctx->context);
        pw_loop_destroy(ctx->source->loop);
        g_main_loop_unref(ctx->main_loop);

        err = "pw_core_get_registry failed";
        goto __err;
    }

    spa_zero(ctx->registry_listener);
    int res = pw_registry_add_listener(ctx->registry, &ctx->registry_listener,
                                       &REGISTRY_EVENTS, ctx);
    if (res < 0)
    {
        pw_core_disconnect(ctx->core);
        pw_context_destroy(ctx->context);
        pw_loop_destroy(ctx->source->loop);
        g_main_loop_unref(ctx->main_loop);

        g_error("pw_registry_add_listener failed: %s", spa_strerror(res));
        return false;
    }

    *context = ctx;
    return true;

__err:
    pw_deinit();
    g_free(ctx);
    *context = nullptr;

    g_error("%s", err == nullptr ? "no error" : err);
    return false;
}


void
volume_logic_init(struct VolumeLogicContext **ctx)
{
    if (!volume_logic_init_pw(ctx)) return;

    (*ctx)->interfaces
        = g_ptr_array_new();
    (*ctx)->interface_datas = g_ptr_array_new();
}


void
volume_logic_deinit(struct VolumeLogicContext *ctx)
{
    pw_core_disconnect(ctx->core);
    pw_context_destroy(ctx->context);
    pw_loop_destroy(ctx->source->loop);
    g_main_loop_unref(ctx->main_loop);

    g_ptr_array_free(ctx->interfaces, FALSE);
    g_ptr_array_free(ctx->interface_datas, FALSE);

    pw_deinit();
    g_free(ctx);
}


void
volume_logic_add_interface(struct VolumeLogicContext         *ctx,
                           const struct VolumeLogicInterface *interface,
                           gpointer                           data)
{
    g_ptr_array_add(ctx->interfaces, (gpointer)interface);
    g_ptr_array_add(ctx->interface_datas, data);
}
