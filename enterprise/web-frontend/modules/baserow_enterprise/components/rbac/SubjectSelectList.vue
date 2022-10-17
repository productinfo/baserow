<template>
  <div>
    <input
      v-model="activeSearchTerm"
      type="text"
      class="input input--large"
      :placeholder="
        $t('SubjectSelectList.searchPlaceholder', { subjectTypeName })
      "
      @keyup="search(activeSearchTerm)"
    />
    <div class="margin-top-2">
      {{
        $t('SubjectSelectList.selectedAmountLabel', {
          subjectsSelectedCount: subjectsSelectedCount || 0,
          subjectTypeName,
        })
      }}
    </div>
    <List
      class="margin-top-2"
      :items="subjectsFiltered"
      :attributes="remainingAttributes"
      selectable
      @selected="subjectSelected"
    >
      <template #left-side="{ item }">
        <span class="margin-left-1">
          {{ item[primaryAttribute] }}
        </span>
      </template>
    </List>
    <a
      class="button"
      :class="{ disabled: !inviteButtonEnabled }"
      @click="invite"
      >{{
        $t('SubjectSelectList.invite', {
          subjectsSelectedCount,
          subjectTypeName,
        })
      }}</a
    >
  </div>
</template>

<script>
export default {
  name: 'SubjectSelectList',
  props: {
    subjects: {
      type: Array,
      required: false,
      default: () => [],
    },
    subjectTypeName: {
      type: String,
      required: true,
    },
    primaryAttribute: {
      type: String,
      required: true,
    },
    remainingAttributes: {
      type: Array,
      required: false,
      default: () => null,
    },
  },
  data() {
    return {
      subjectsFiltered: this.subjects,
      subjectsSelected: [],
      activeSearchTerm: null,
    }
  },
  computed: {
    attributes() {
      return [this.primaryAttribute].concat(this.remainingAttributes)
    },
    subjectsSelectedCount() {
      return this.subjectsSelected.length !== 0
        ? this.subjectsSelected.length
        : null
    },
    inviteButtonEnabled() {
      return this.subjectsSelectedCount !== null
    },
  },
  methods: {
    search(value) {
      if (value === null || value === '') {
        this.subjectsFiltered = this.subjects
      }

      const attributes = this.attributes ?? Object.keys(this.subjects[0])

      attributes.some((attribute) => {
        return this.subjects[0][attribute].includes(value)
      })

      this.subjectsFiltered = this.subjects.filter((subject) =>
        attributes.some((attribute) => subject[attribute].includes(value))
      )
    },
    subjectSelected({ value, item }) {
      if (value) {
        this.subjectsSelected.push(item)
      } else {
        const index = this.subjectsSelected.findIndex(
          (subject) =>
            subject[this.primaryAttribute] === item[this.primaryAttribute]
        )
        this.subjectsSelected.splice(index, 1)
      }
    },
    invite() {
      if (this.inviteButtonEnabled) {
        this.$emit('invite', this.subjectsSelected)
      }
    },
  },
}
</script>
