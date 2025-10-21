#pragma once
#ifdef VOLUME_TAB

struct TabWidget;


void volume_tab_new(struct TabWidget *tab_data);
void volume_tab_delete(struct TabWidget *tab_data);

#else

#define volume_tab_new(x) ((void)0)
#define volume_tab_delete(x) ((void)0)

#endif
