<template functional>
  <div class="card-multiple-collaborators__list-wrapper">
    <div class="card-multiple-collaborators__list">
      <div
        v-for="item in props.value"
        :key="item.id"
        class="card-multiple-collaborators__item"
      >
        <div v-if="props.value" class="field-multiple-collaborators__initials">
          {{ $options.methods.initial(item.name) }}
        </div>
        <span
          class="
            field-multiple-collaborators__name
            background-color--light-gray
          "
          >{{ item.name }}</span
        >
      </div>
    </div>
  </div>
</template>

<script>
export default {
  height: 30,
  methods: {
    initial(name) {
      return name.slice(0, 1).toUpperCase()
    },
  },
}
</script>
