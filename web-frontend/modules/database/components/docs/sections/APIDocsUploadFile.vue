<template>
  <div class="api-docs__item">
    <div class="api-docs__left">
      <div class="api-docs__heading-wrapper">
        <h3 :id="'section-upload-file'" class="api-docs__heading-3">
          <span>
            {{ $t('apiDocs.uploadFile') }}
          </span>
        </h3>
        <div class="api-docs__endpoint-type"></div>
      </div>

      <p class="api-docs__content">
        {{ $t('apiDocsUploadFile.description') }}
      </p>

      <h4 class="api-docs__heading-4">{{ $t('apiDocs.queryParameters') }}</h4>
      <ul class="api-docs__parameters">
        <APIDocsParameter name="file" :optional="false" type="multipart">
          <MarkdownIt
            class="api-docs__content"
            :content="
              $t('apiDocs.uploadFileDescription', {
                PUBLIC_BACKEND_URL: getPublicBackendUrl(),
              })
            "
          />
        </APIDocsParameter>
      </ul>
    </div>

    <div class="api-docs__right">
      <APIDocsExample
        :value="value"
        type="POST"
        :url="getUploadFileListUrl()"
        :file="getUploadFileExample()"
        :response="getFileUploadResponse()"
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
  name: 'APIDocsUploadFile',
  components: {
    APIDocsParameter,
    APIDocsExample,
  },
  props: {
    value: {
      type: Object,
      required: true,
    },
    getPublicBackendUrl: { type: Function, required: true },
    getUploadFileListUrl: { type: Function, required: true },
    getUploadFileExample: { type: Function, required: true },
    getFileUploadResponse: { type: Function, required: true },
  },
}
</script>
