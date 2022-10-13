<template>
  <div>
    <div class="box__head-logo">
      <nuxt-link :to="{ name: 'index' }">
        <img src="@baserow/modules/core/static/img/logo.svg" alt="" />
      </nuxt-link>
    </div>
    <div class="login-box__head">
      <h1 class="box__head-title">
        {{ $t('enterprise.loginError.title') }}
      </h1>
    </div>
    {{ errorMessage }}
  </div>
</template>

<script>
export default {
  layout: 'login',
  asyncData({ route, i18n }) {
    return {
      errorMessage:
        route.query.message || i18n.t('enterprise.loginError.defaultMessage'),
    }
  },
  head() {
    return {
      title: this.$t('enterprise.loginError.title'),
    }
  },
}
</script>
