<template functional>
    <div
      :style="{'text-overflow': 'ellipsis', overflow: 'hidden', 'white-space': 'nowrap', 'line-height': '22px', 'max-width': '480px'}" 
      :class="[data.staticClass, data.class]"
      :title="props.row[props.column.key]"
      v-on="listeners"
    >
      {{ props.row[props.column.key] }}
    </div>
  </template>
  
  <script>
  export default {
    name: 'LongTextField',
    functional: true,
    props: {
      row: {
        required: true,
        type: Object,
      },
      column: {
        required: true,
        type: Object,
      },
    },
  }
  </script>
  