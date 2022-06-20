<template>
  <div class="preview__text-wrapper">
    <object class="preview__text" :data="url"></object>
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
}
</script>
