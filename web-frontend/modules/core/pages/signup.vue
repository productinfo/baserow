<template>
  <div>
    <h1 class="box-title">Sign up</h1>
    <Error :error="error"></Error>
    <form @submit.prevent="register">
      <div class="control">
        <label class="control-label">E-mail address</label>
        <div class="control-elements">
          <input
            ref="email"
            v-model="account.email"
            :class="{ 'input-error': $v.account.email.$error }"
            type="text"
            class="input input-large"
            @blur="$v.account.email.$touch()"
          />
          <div v-if="$v.account.email.$error" class="error">
            Please enter a valid e-mail address.
          </div>
        </div>
      </div>
      <div class="control">
        <label class="control-label">Your name</label>
        <div class="control-elements">
          <input
            v-model="account.name"
            :class="{ 'input-error': $v.account.name.$error }"
            type="text"
            class="input input-large"
            @blur="$v.account.name.$touch()"
          />
          <div v-if="$v.account.name.$error" class="error">
            A minimum of two characters is required here.
          </div>
        </div>
      </div>
      <div class="control">
        <label class="control-label">Password</label>
        <div class="control-elements">
          <input
            v-model="account.password"
            :class="{ 'input-error': $v.account.password.$error }"
            type="password"
            class="input input-large"
            @blur="$v.account.password.$touch()"
          />
          <div v-if="$v.account.password.$error" class="error">
            A password is required.
          </div>
        </div>
      </div>
      <div class="control">
        <label class="control-label">Repeat password</label>
        <div class="control-elements">
          <input
            v-model="account.passwordConfirm"
            :class="{ 'input-error': $v.account.passwordConfirm.$error }"
            type="password"
            class="input input-large"
            @blur="$v.account.passwordConfirm.$touch()"
          />
          <div v-if="$v.account.passwordConfirm.$error" class="error">
            This field must match your password field.
          </div>
        </div>
      </div>
      <div class="actions">
        <ul class="action-links">
          <li>
            <nuxt-link :to="{ name: 'login' }">
              <i class="fas fa-arrow-left"></i>
              Back
            </nuxt-link>
          </li>
        </ul>
        <button
          :class="{ 'button-loading': loading }"
          class="button button-large"
          :disabled="loading"
        >
          Sign up
          <i class="fas fa-user-plus"></i>
        </button>
      </div>
    </form>
  </div>
</template>

<script>
import { required, email, sameAs, minLength } from 'vuelidate/lib/validators'

import { ResponseErrorMessage } from '@baserow/modules/core/plugins/clientHandler'
import error from '@baserow/modules/core/mixins/error'

export default {
  layout: 'login',
  mixins: [error],
  head() {
    return {
      title: 'Create new account'
    }
  },
  validations: {
    account: {
      email: { required, email },
      name: {
        required,
        minLength: minLength(2)
      },
      password: { required },
      passwordConfirm: {
        sameAsPassword: sameAs('password')
      }
    }
  },
  data() {
    return {
      loading: false,
      account: {
        email: '',
        name: '',
        password: '',
        passwordConfirm: ''
      }
    }
  },
  methods: {
    async register() {
      this.$v.$touch()
      if (this.$v.$invalid) {
        return
      }

      this.loading = true
      this.hideError()

      try {
        await this.$store.dispatch('auth/register', {
          name: this.account.name,
          email: this.account.email,
          password: this.account.password
        })
        this.$nuxt.$router.push({ name: 'dashboard' })
      } catch (error) {
        this.loading = false
        this.handleError(error, 'signup', {
          ERROR_EMAIL_ALREADY_EXISTS: new ResponseErrorMessage(
            'User already exists.',
            'A user with the provided e-mail address already exists.'
          )
        })
      }
    }
  }
}
</script>
