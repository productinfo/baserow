<template>
  <div>
    <a
      class="auth-provider-buttons__button"
      :href="`${redirectUrl}`"
      target="_self"
    >
      Continue with {{ name }}
    </a>
  </div>
</template>

<script>
export default {
  name: 'OAuth2LoginButton',
  props: {
    redirectUrl: {
      type: String,
      required: true,
    },
    name: {
      type: String,
      required: true,
    },
  },
}
</script>
