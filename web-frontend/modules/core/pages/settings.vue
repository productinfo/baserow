<template>
  <div>
    <ul class="tabs">
      <li
        class="tabs__item-selector"
        :class="{ 'tabs__item-selector--active': true }"
      >
        <nuxt-link
          :to="{
            name: 'settings-members',
            params: {
              groupId: group.id,
            },
          }"
          class="tabs__link"
        >
          {{ $t('membersSettings.membersTabTitle') }}
        </nuxt-link>
      </li>
      <li
        class="tabs__item-selector"
        :class="{ 'tabs__item-selector--active': false }"
      >
        <nuxt-link
          :to="{
            name: 'settings-invites',
            params: {
              groupId: group.id,
            },
          }"
          class="tabs__link"
        >
          {{ $t('membersSettings.invitesTabTitle') }}
        </nuxt-link>
      </li>
    </ul>
    <NuxtChild :group="group" />
  </div>
</template>

<script>
export default {
  name: 'Settings',
  layout: 'app',
  computed: {
    group() {
      return this.$store.getters['group/get'](
        parseInt(this.$route.params.groupId, 10)
      )
    },
  },
}
</script>
