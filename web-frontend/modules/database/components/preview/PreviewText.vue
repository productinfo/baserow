<template>
  <div v-if="!fileFetchFailed" class="preview__text">
    {{ text }}
  </div>
  <div v-else class="preview__text--failed">
    <i class="fas fa-exclamation-circle"></i>
  </div>
</template>

<script>
export default {
  name: 'PreviewText',
  props: {
    url: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      text: null,
      fileFetchFailed: false,
    }
  },
  async created() {
    try {
      this.text = (await (await fetch(this.url)).text()) || ''
    } catch (error) {
      await this.$store.dispatch('notification/error', {
        title: this.$t('previewText.error.title'),
        message: this.$t('previewText.error.message'),
      })
      this.fileFetchFailed = true
    }
  },
}
</script>
