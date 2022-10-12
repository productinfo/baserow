<template>
  <div class="sso__admin-list-item">
    <div class="sso__admin-list-item-name">
      <i class="sso__admin-list-item-icon" :class="getIconClass()" />
      {{ getProviderName() }}
    </div>
    <div class="sso__admin-list-item-menu">edit</div>
    <SwitchInput
      class="sso__admin-list-item-toggle"
      :value="provider.enabled"
      :large="true"
      @input="setProviderEnabled($event)"
    ></SwitchInput>
  </div>
</template>

<script>
import SwitchInput from '@baserow/modules/core/components/SwitchInput.vue'

export default {
  name: 'ProviderListItem',
  components: { SwitchInput },
  props: {
    provider: {
      type: Object,
      required: true,
    },
  },
  methods: {
    getIconClass() {
      return this.$registry
        .get('authProvider', this.provider.type)
        .getIconClass()
    },
    getProviderName() {
      return this.$registry
        .get('authProvider', this.provider.type)
        .getProviderName(this.provider)
    },
    setProviderEnabled(enabled) {
      console.log(enabled)
    },
  },
}
</script>
