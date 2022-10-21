<template>
  <TeamsTable :group="group" />
</template>

<script>
import TeamsTable from '@baserow_enterprise/components/teams/TeamsTable'

export default {
  name: 'Teams',
  components: { TeamsTable },
  props: {
    group: {
      type: Object,
      required: true,
    },
  },
}
</script>
