<template>
  <div>
    <div class="layout__col-2-1">
      <ul class="page-tabs">
        <nuxt-link
          v-slot="{ href, navigate, isExactActive }"
          :to="{
            name: 'settings-members',
            params: {
              groupId: group.id,
            },
          }"
        >
          <li
            class="page-tabs__item"
            :class="{ 'page-tabs__item--active': isExactActive }"
          >
            <a :href="href" class="page-tabs__link" @click="navigate">
              {{ $t('membersSettings.membersTabTitle') }}
            </a>
          </li>
        </nuxt-link>
        <nuxt-link
          v-slot="{ href, navigate, isExactActive }"
          :to="{
            name: 'settings-invites',
            params: {
              groupId: group.id,
            },
          }"
        >
          <li
            class="page-tabs__item"
            :class="{ 'page-tabs__item--active': isExactActive }"
          >
            <a :href="href" class="page-tabs__link" @click="navigate">
              {{ $t('membersSettings.invitesTabTitle') }}
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
  computed: {
    group() {
      return this.$store.getters['group/get'](
        parseInt(this.$route.params.groupId, 10)
      )
    },
  },
}
</script>
