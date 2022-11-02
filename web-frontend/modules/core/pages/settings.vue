<template>
  <div>
    <div class="layout__col-2-1">
      <ul class="page-tabs">
        <nuxt-link
          v-for="page in pages"
          :key="page.type"
          v-slot="{ href, navigate, isExactActive }"
          :to="page.to"
        >
          <li
            class="page-tabs__item"
            :class="{ 'page-tabs__item--active': isExactActive }"
          >
            <a :href="href" class="page-tabs__link" @click="navigate">
              {{ page.name }}
            </a>
          </li>
        </nuxt-link>
      </ul>
    </div>
    <div class="layout__col-2-2">
      <NuxtChild :group="group" />
    </div>
  </div>
</template>

<script>
export default {
  name: 'Settings',
  layout: 'app',
  asyncData({ store, params, error }) {
    const group = store.getters['group/get'](parseInt(params.groupId, 10))

    if (group === undefined) {
      return error({ statusCode: 404, message: 'Group not found.' })
    }

    return { group }
  },
  computed: {
    groupSettingsPageTypes() {
      return this.$registry.getAll('groupSettingsPage')
    },
    pages() {
      return Object.values(this.groupSettingsPageTypes).map((instance) => {
        return {
          type: instance.type,
          name: instance.getName(),
          to: instance.getRoute(this.group),
        }
      })
    },
  },
}
</script>
