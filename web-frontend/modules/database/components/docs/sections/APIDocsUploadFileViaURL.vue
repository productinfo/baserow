<template>
    <div class="api-docs__item">
        <div class="api-docs__left">
            <div class="api-docs__heading-wrapper">
                <h3 :id="'section-table-' + table.id + '-upload-file-via-url'" class="api-docs__heading-3">
                    <span>
                        {{ $t('apiDocs.uploadFileViaUrl') }}
                    </span>
                </h3>
                <div class="api-docs__endpoint-type"></div>
            </div>

            <p class="api-docs__content">
                {{ $t('apiDocsUploadFileViaURL.description', table) }}
            </p>

            <h4 class="api-docs__heading-4">{{ $t('apiDocs.queryParameters') }}</h4>
            <ul class="api-docs__parameters">
                <APIDocsParameter name="url" :optional="false" type="string">
                <MarkdownIt
                    class="api-docs__content"
                    :content="$t('apiDocs.uploadFileViaUrlDescription')"
                />
                </APIDocsParameter>
            </ul>
        </div>

        <div class="api-docs__right">
            <APIDocsExample
                :value="value"
                type="POST"
                :url="getUploadFileViaUrlListUrl(table)"
                :include-user-fields-checkbox="false"
                @input="$emit('input', $event)"
            ></APIDocsExample>
        </div>
    </div>
</template>

<script>
import APIDocsExample from '@baserow/modules/database/components/docs/APIDocsExample'
import APIDocsParameter from '@baserow/modules/database/components/docs/APIDocsParameter'

export default {
    name: 'apiDocsUploadFileViaURL',
    components: {
        APIDocsParameter,
        APIDocsExample,
    },
    props: {
        value: {
            type: Object,
            required: true,
        },
        table: { type: Object, required: true },
        getUploadFileViaUrlListUrl: { type: Function, required: true },
    },
    data() {
        return {
            batchMode: false,
        }
    },
}
</script>
