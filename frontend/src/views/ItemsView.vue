<script setup lang="ts">
import client from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const auth = useAuthStore()

interface Item {
  id: number
  sku: string
  status: string
  warehouse_id: number
}

// Campos y operadores disponibles para el filtro — alineados con el contrato del backend
const OPERATORS = ['=', '!=', '>', '<', 'like'] as const
type FilterOperator = (typeof OPERATORS)[number]

const filterField = ref<'status' | 'warehouse_id'>('status')
const filterOperator = ref<FilterOperator>('=')
const filterValue = ref('')

const items = ref<Item[]>([])
const loading = ref(false)
const error = ref('')

async function fetchItems() {
  error.value = ''
  loading.value = true

  // Construye el payload: con filtro si hay valor, sin filtro si está vacío
  const filters =
    filterValue.value.trim()
      ? [{ field: filterField.value, op: filterOperator.value, value: filterValue.value.trim() }]
      : null

  try {
    const response = await client.post('/items/search', { filters })
    items.value = response.data
  } catch (e) {
    if (axios.isAxiosError(e) && e.response?.status === 401) {
      router.push('/login')
    } else {
      error.value = 'Error al cargar los items. Inténtalo de nuevo.'
    }
  } finally {
    loading.value = false
  }
}

function clearFilter() {
  filterField.value = 'status'
  filterOperator.value = '='
  filterValue.value = ''
  fetchItems()
}

async function changeStatus(item: Item, newStatus: string) {
  try {
    // Usamos PATCH en lugar del GET original — semánticamente correcto para mutaciones parciales
    const response = await client.patch(`/items/${item.id}/status`, { status: newStatus })
    const updated = response.data
    // Actualizamos solo la fila afectada sin recargar toda la tabla
    const index = items.value.findIndex((i) => i.id === item.id)
    if (index !== -1) {
      items.value[index] = updated
    }
  } catch {
    error.value = 'No se pudo actualizar el estado del item.'
  }
}

function handleLogout() {
  auth.logout()
  router.push('/login')
}

onMounted(fetchItems)
</script>

<template>
  <div class="page">
    <header>
      <h1>SCM Logística — Items</h1>
      <button class="logout" @click="handleLogout">Cerrar sesión</button>
    </header>

    <main>
      <div class="toolbar">
        <!-- Filtro simple: un campo + operador + valor. -->
        <!-- Campos disponibles alineados con los permitidos por el backend (status, warehouse_id) -->
        <div class="filters">
          <select v-model="filterField">
            <option value="status">Estado</option>
            <option value="warehouse_id">Almacén</option>
          </select>

          <select v-model="filterOperator">
            <option v-for="op in OPERATORS" :key="op" :value="op">{{ op }}</option>
          </select>

          <input
            v-model="filterValue"
            type="text"
            placeholder="Valor..."
            @keyup.enter="fetchItems"
          />

          <button @click="fetchItems" :disabled="loading">
            {{ loading ? 'Buscando...' : 'Buscar' }}
          </button>

          <button class="clear" @click="clearFilter" :disabled="loading">
            Limpiar
          </button>
        </div>
      </div>

      <p v-if="error" class="error">{{ error }}</p>

      <table v-if="items.length > 0">
        <thead>
          <tr>
            <th>ID</th>
            <th>SKU</th>
            <th>Estado</th>
            <th>Almacén</th>
            <th>Cambiar estado</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.id">
            <td>{{ item.id }}</td>
            <td>{{ item.sku }}</td>
            <td>
              <span :class="['badge', item.status]">{{ item.status }}</span>
            </td>
            <td>{{ item.warehouse_id }}</td>
            <td>
              <select
                :value="item.status"
                @change="changeStatus(item, ($event.target as HTMLSelectElement).value)"
              >
                <option value="pending">pending</option>
                <option value="done">done</option>
                <option value="cancelled">cancelled</option>
              </select>
            </td>
          </tr>
        </tbody>
      </table>

      <p v-else-if="!loading">No hay items para mostrar. Pulsa "Buscar items".</p>
    </main>
  </div>
</template>

<style scoped>
.page {
  max-width: 900px;
  margin: 0 auto;
  padding: 1.5rem;
}

header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

h1 {
  font-size: 1.25rem;
  font-weight: 600;
}

.logout {
  padding: 0.4rem 0.875rem;
  background: transparent;
  border: 1px solid #dc2626;
  color: #dc2626;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
}

.logout:hover {
  background: #dc2626;
  color: white;
}

.toolbar {
  margin-bottom: 1rem;
}

.toolbar button {
  padding: 0.5rem 1rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
}

.toolbar button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

th, td {
  text-align: left;
  padding: 0.625rem 0.75rem;
  border-bottom: 1px solid #e5e7eb;
}

th {
  background: #f9fafb;
  font-weight: 600;
}

.badge {
  padding: 0.2rem 0.5rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 500;
}

.badge.pending  { background: #fef3c7; color: #92400e; }
.badge.done     { background: #d1fae5; color: #065f46; }
.badge.cancelled { background: #fee2e2; color: #991b1b; }

select {
  padding: 0.25rem 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.875rem;
}

.error {
  color: #dc2626;
  margin-bottom: 1rem;
}

.filters {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  flex-wrap: wrap;
}

.filters select,
.filters input {
  padding: 0.4rem 0.6rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.875rem;
}

.filters input {
  min-width: 140px;
}

.filters button {
  padding: 0.4rem 0.875rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
}

.filters button.clear {
  background: transparent;
  border: 1px solid #6b7280;
  color: #6b7280;
}

.filters button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
