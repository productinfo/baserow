<template>
  <div>
    <object :width="500" :height="500" :data="url"></object>
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
