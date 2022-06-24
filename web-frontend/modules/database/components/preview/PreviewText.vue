<template>
  <div class="preview__text-wrapper">
    {{ text }}
  </div>
</template>

<script>
import { notifyIf } from '@baserow/modules/core/utils/error'

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
    }
  },
  async created() {
    try {
      this.text = (await this.$client.get(this.url)).data
    } catch (error) {
      notifyIf(error)
    }
  },
}
</script>
