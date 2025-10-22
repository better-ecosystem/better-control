#pragma once
#include <glib.h>

struct VolumeLogicContext;


void volume_logic_init(struct VolumeLogicContext **ctx);
void volume_logic_deinit(struct VolumeLogicContext *ctx);


typedef enum
{
    VOLUME_SINK   = 0,
    VOLUME_SOURCE = 1,
} VolumeType;

struct VolumeLogicInterface
{
    void (*on_volume_change)(VolumeType type, float volume, guint32 id,
                             gpointer data);

    void (*on_device_added)(VolumeType type, guint32 id, const char *name,
                            gpointer data);

    void (*on_device_remove)(guint32 id, gpointer data);

    void (*set_volume)(VolumeType type, float volume, guint32 id,
                       gpointer data);
};


void volume_logic_add_interface(struct VolumeLogicContext         *ctx,
                                const struct VolumeLogicInterface *interface,
                                gpointer                           data);
