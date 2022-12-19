<template>
    <div class="filter-wrapper">
        <div class="filter-wrapper__title">{{ name }}</div>
        <slot></slot>
    </div>
</template>

<script>
export default {
    name: 'FilterWrapper',
    props: {
        name: {
            type: String,
            required: true,
        },
    }
}
</script>