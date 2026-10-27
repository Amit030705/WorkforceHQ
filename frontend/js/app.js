const state = { user: null, page: 'dashboard', editor: null, toastTimer: null };
const view = document.querySelector('#view');
const editor = document.querySelector('#editor');
const editorBody = document.querySelector('#editor-body');
const editorForm = document.querySelector('#editor-form');
const navigation = document.querySelector('#navigation');
const navItems = [
	{ id: 'dashboard', label: 'Dashboard', icon: '▦', admin: true },
	{ id: 'employees', label: 'Employees', icon: '♙', admin: true },
	{ id: 'departments', label: 'Departments', icon: '▤', admin: true },
	{ id: 'attendance', label: 'Attendance', icon: '◷' },
	{ id: 'leaves', label: 'Leave requests', icon: '▧' },
	{ id: 'profile', label: 'My profile', icon: '◎', employee: true },
];
const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, (char) => (
	{ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]
));
const titleCase = (value) => String(value).replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
const dateText = (value) => value ? new Date(`${value}T00:00:00`).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' }) : '—';
const today = () => new Date().toISOString().slice(0, 10);

async function api(path, options = {}) {
	const headers = new Headers(options.headers || {});
	if (options.body && typeof options.body !== 'string' && !(options.body instanceof FormData)) {
		headers.set('Content-Type', 'application/json');
		options.body = JSON.stringify(options.body);
	}
	const response = await fetch(`/api/v1${path}`, { ...options, headers, credentials: 'same-origin' });
	if (response.status === 204) return null;
	const result = await response.json().catch(() => ({}));
	if (response.status === 401) {
		window.location.replace('/login');
		throw new Error('Your session expired. Please sign in again.');
	}
	if (!response.ok) throw new Error(formatError(result.detail));
	return result;
}

function formatError(detail) {
	if (typeof detail === 'string') return detail;
	if (Array.isArray(detail)) return detail.map((item) => `${item.loc?.slice(-1)[0] || 'Field'}: ${item.msg}`).join(' · ');
	return 'Something went wrong. Please try again.';
}

function toast(message, error = false) {
	const element = document.querySelector('#toast');
	element.textContent = message;
	element.style.background = error ? '#9d3241' : '#1d2b41';
	element.classList.add('show');
	clearTimeout(state.toastTimer);
	state.toastTimer = setTimeout(() => element.classList.remove('show'), 3200);
}

function showError(error) {
	view.innerHTML = `<div class="notice">${escapeHtml(error.message)}</div><button class="button button-light" data-action="refresh">Try again</button>`;
}

async function start() {
	document.querySelector('#top-date').textContent = new Date().toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' });
	try {
		state.user = await api('/auth/me');
		if (!state.user) return;
		document.querySelector('#account-name').textContent = state.user.employee_name || state.user.email;
		document.querySelector('#account-role').textContent = titleCase(state.user.role);
		document.querySelector('#avatar').textContent = (state.user.employee_name || state.user.email)[0].toUpperCase();
		if (state.user.role !== 'admin') state.page = 'profile';
		drawNavigation();
		await renderPage();
	} catch (error) {
		if (!window.location.pathname.endsWith('/login')) window.location.replace('/login');
	}
}

function drawNavigation() {
	const items = navItems.filter((item) => item.admin ? state.user.role === 'admin' : item.employee ? state.user.role !== 'admin' : true);
	navigation.innerHTML = items.map((item) => `<button class="nav-item ${state.page === item.id ? 'active' : ''}" data-page="${item.id}"><span class="nav-icon">${item.icon}</span>${item.label}</button>`).join('');
}

function heading(eyebrow, title, description, action = '') {
	return `<div class="page-heading"><div><div class="eyebrow">${escapeHtml(eyebrow)}</div><h1>${escapeHtml(title)}</h1><p>${escapeHtml(description)}</p></div>${action}</div>`;
}

function panel(title, subtitle, body, actions = '') {
	return `<section class="panel"><div class="panel-header"><div><h2>${escapeHtml(title)}</h2>${subtitle ? `<p>${escapeHtml(subtitle)}</p>` : ''}</div>${actions}</div>${body}</section>`;
}

function statusBadge(value) {
	return `<span class="status-badge status-${escapeHtml(value)}">${escapeHtml(titleCase(value))}</span>`;
}

function formatPerson(name, email) {
	return `<div class="person-cell"><span class="tiny-avatar">${escapeHtml((name || '?')[0].toUpperCase())}</span><span class="person-meta"><strong>${escapeHtml(name)}</strong><small>${escapeHtml(email)}</small></span></div>`;
}

async function renderPage() {
	drawNavigation();
	document.querySelector('#breadcrumb').textContent = navItems.find((item) => item.id === state.page)?.label || 'Workspace';
	view.innerHTML = '<div class="loading-state">Loading your workspace…</div>';
	try {
		switch (state.page) {
			case 'dashboard': await renderDashboard(); break;
			case 'employees': await renderEmployees(); break;
			case 'departments': await renderDepartments(); break;
			case 'attendance': await renderAttendance(); break;
			case 'leaves': await renderLeaves(); break;
			case 'profile': await renderProfile(); break;
			default: state.page = state.user.role === 'admin' ? 'dashboard' : 'profile'; await renderPage();
		}
	} catch (error) {
		showError(error);
	}
}

async function renderDashboard() {
	const stats = await api('/dashboard/stats');
	const cards = [
		['Total employees', stats.total_employees, '♙', 'All employee profiles'],
		['Active employees', stats.active_employees, '✓', 'Currently active'],
		['Departments', stats.total_departments, '▤', 'Teams and functions'],
		['Present today', stats.employees_present_today, '◷', dateText(today())],
		['Pending leave', stats.pending_leave_requests, '▧', 'Awaiting admin review'],
	];
	const cardHtml = cards.map(([label, value, icon, foot]) => `<article class="stat-card"><div class="stat-top">${label}<span class="stat-icon">${icon}</span></div><div class="stat-value">${value}</div><div class="stat-foot">${escapeHtml(foot)}</div></article>`).join('');
	view.innerHTML = `${heading('PEOPLE OVERVIEW', 'Good to see you, ' + (state.user.employee_name || 'Administrator').split(' ')[0], 'Here is the current overview of your organization.')}<div class="stats-grid">${cardHtml}</div>${panel('Quick actions', 'Manage your people and daily activity', `<div class="panel-body quick-actions"><button class="button button-light" data-page="employees">View employees →</button><button class="button button-light" data-page="attendance">Record attendance →</button><button class="button button-light" data-page="leaves">Review leave requests →</button></div>`)}`;
}

function openEditor(title, fields, values, saveLabel = 'Save changes') {
	state.editor = { fields, values };
	editorBody.innerHTML = `<h2>${escapeHtml(title)}</h2><div class="form-grid">${fields.map((field) => {
		const value = values[field.name] ?? '';
		if (field.type === 'select') return `<label class="${field.full ? 'full' : ''}">${escapeHtml(field.label)}<select name="${field.name}" ${field.required ? 'required' : ''}>${field.options.map((option) => `<option value="${escapeHtml(option.value)}" ${String(value) === String(option.value) ? 'selected' : ''}>${escapeHtml(option.label)}</option>`).join('')}</select></label>`;
		if (field.type === 'textarea') return `<label class="${field.full ? 'full' : ''}">${escapeHtml(field.label)}<textarea name="${field.name}" ${field.required ? 'required' : ''} maxlength="${field.maxlength || 3000}">${escapeHtml(value)}</textarea></label>`;
		return `<label class="${field.full ? 'full' : ''}">${escapeHtml(field.label)}<input name="${field.name}" type="${field.type || 'text'}" value="${escapeHtml(value)}" ${field.required ? 'required' : ''} ${field.min !== undefined ? `min="${field.min}"` : ''} ${field.maxlength ? `maxlength="${field.maxlength}"` : ''} ${field.step ? `step="${field.step}"` : ''} ${field.autocomplete ? `autocomplete="${field.autocomplete}"` : ''} /></label>`;
	}).join('')}</div>`;
	document.querySelector('#save-editor').textContent = saveLabel;
	editor.showModal();
}

function employeeFields(departments, employee = {}) {
	return [
		{ name: 'employee_code', label: 'Employee ID', required: true, maxlength: 40 },
		{ name: 'name', label: 'Full name', required: true, maxlength: 160 },
		{ name: 'email', label: 'Work email', type: 'email', required: true },
		{ name: 'phone', label: 'Phone number', maxlength: 32 },
		{ name: 'department_id', label: 'Department', type: 'select', required: true, options: departments.map((item) => ({ value: item.id, label: item.name })) },
		{ name: 'designation', label: 'Designation', required: true },
		{ name: 'joining_date', label: 'Joining date', type: 'date', required: true },
		{ name: 'salary', label: 'Annual salary', type: 'number', min: 0, step: '.01', required: true },
		{ name: 'employment_status', label: 'Employment status', type: 'select', options: ['active', 'inactive', 'on_leave', 'terminated'].map((value) => ({ value, label: titleCase(value) })) },
		...(!employee.id ? [{ name: 'password', label: 'Initial password (12 characters minimum)', type: 'password', required: true, maxlength: 128, autocomplete: 'new-password', full: true }] : []),
	];
}

async function renderEmployees(filters = {}) {
	const params = new URLSearchParams({ page: String(filters.page || 1), page_size: '20' });
	if (filters.search) params.set('search', filters.search);
	if (filters.department_id) params.set('department_id', filters.department_id);
	if (filters.employment_status) params.set('employment_status', filters.employment_status);
	const [data, departments] = await Promise.all([api(`/employees?${params}`), api('/departments?page_size=100')]);
	const action = '<button class="button button-primary" data-action="add-employee">＋ Add employee</button>';
	const tableRows = data.items.map((item) => `<tr><td>${formatPerson(item.name, item.email)}</td><td><strong>${escapeHtml(item.employee_code)}</strong></td><td>${escapeHtml(item.department_name)}</td><td>${escapeHtml(item.designation)}</td><td>${dateText(item.joining_date)}</td><td>${statusBadge(item.employment_status)}</td><td><div class="table-actions"><button class="button button-light button-small" data-action="edit-employee" data-id="${item.id}">Edit</button><button class="button button-danger button-small" data-action="delete-employee" data-id="${item.id}">Delete</button></div></td></tr>`).join('');
	const lastPage = Math.max(1, Math.ceil(data.total / data.page_size));
	state.employeeFilters = { ...filters, page: data.page };
	const table = `<div class="toolbar"><input id="employee-search" placeholder="Search name, email, or ID" value="${escapeHtml(filters.search || '')}" /><select id="department-filter"><option value="">All departments</option>${departments.items.map((dep) => `<option value="${dep.id}" ${String(filters.department_id) === String(dep.id) ? 'selected' : ''}>${escapeHtml(dep.name)}</option>`).join('')}</select><select id="status-filter"><option value="">All statuses</option>${['active', 'inactive', 'on_leave', 'terminated'].map((value) => `<option value="${value}" ${filters.employment_status === value ? 'selected' : ''}>${titleCase(value)}</option>`).join('')}</select><button class="button button-light" data-action="filter-employees">Filter</button><span class="muted">${data.total} employee${data.total === 1 ? '' : 's'}</span></div><div class="table-wrap"><table><thead><tr><th>Employee</th><th>Employee ID</th><th>Department</th><th>Designation</th><th>Joining date</th><th>Status</th><th>Actions</th></tr></thead><tbody>${tableRows || '<tr><td colspan="7" class="empty-state">No employees found. Add your first employee to get started.</td></tr>'}</tbody></table></div><div class="toolbar"><button class="button button-light button-small" data-action="employee-page" data-page-number="${Math.max(1, data.page - 1)}" ${data.page <= 1 ? 'disabled' : ''}>← Previous</button><span class="muted">Page ${data.page} of ${lastPage}</span><button class="button button-light button-small" data-action="employee-page" data-page-number="${Math.min(lastPage, data.page + 1)}" ${data.page >= lastPage ? 'disabled' : ''}>Next →</button></div>`;
	view.innerHTML = `${heading('YOUR PEOPLE', 'Employees', 'View and manage employee profiles, departments, and work details.', action)}${panel('Employee directory', 'Search, filter, and manage employee information', table)}`;
}

async function renderDepartments() {
	const data = await api('/departments?page_size=100');
	const rows = data.items.map((item) => `<tr><td><strong>${escapeHtml(item.name)}</strong></td><td>${escapeHtml(item.description || '—')}</td><td>${item.employee_count}</td><td><div class="table-actions"><button class="button button-light button-small" data-action="edit-department" data-id="${item.id}">Edit</button><button class="button button-danger button-small" data-action="delete-department" data-id="${item.id}">Delete</button></div></td></tr>`).join('');
	view.innerHTML = `${heading('ORGANIZATION', 'Departments', 'Group employees into teams and business functions.', '<button class="button button-primary" data-action="add-department">＋ Add department</button>')}${panel('Department directory', 'Departments with employee counts', `<div class="table-wrap"><table><thead><tr><th>Department</th><th>Description</th><th>Employees</th><th>Actions</th></tr></thead><tbody>${rows || '<tr><td colspan="4" class="empty-state">No departments yet. Add one to organize your team.</td></tr>'}</tbody></table></div>`)}`;
}

async function renderAttendance() {
	const employees = state.user.role === 'admin' ? await api('/employees?page_size=100') : { items: [] };
	state.attendanceEmployees = employees.items;
	await renderAttendanceFilter(state.attendanceFilters || { start_date: today(), end_date: today() });
}

async function renderAttendanceFilter(filters) {
	state.attendanceFilters = filters;
	const query = new URLSearchParams({ page_size: '100' });
	if (filters.start_date) query.set('start_date', filters.start_date);
	if (filters.end_date) query.set('end_date', filters.end_date);
	if (filters.employee_id) query.set('employee_id', filters.employee_id);
	const [data, summary] = await Promise.all([
		api(`/attendance?${query}`),
		api(`/attendance/summary?${query}`),
	]);
	let action = '';
	if (state.user.role === 'admin') action = '<button class="button button-primary" data-action="record-attendance">＋ Record attendance</button>';
	const rows = data.items.map((item) => `<tr><td>${formatPerson(item.employee_name, `Employee #${item.employee_id}`)}</td><td>${dateText(item.attendance_date)}</td><td>${statusBadge(item.status)}</td><td>${escapeHtml(item.notes || '—')}</td></tr>`).join('');
	const summaryLine = ['present', 'absent', 'late', 'half_day'].map((key) => `${titleCase(key)}: <strong>${summary[key]}</strong>`).join('　·　');
	const employeeFilter = state.user.role === 'admin' ? `<select id="attendance-employee"><option value="">All employees</option>${state.attendanceEmployees.map((item) => `<option value="${item.id}" ${String(filters.employee_id || '') === String(item.id) ? 'selected' : ''}>${escapeHtml(item.name)}</option>`).join('')}</select>` : '';
	const toolbar = `<div class="toolbar"><label class="filter-label">From<input type="date" id="attendance-start" value="${escapeHtml(filters.start_date || '')}" /></label><label class="filter-label">To<input type="date" id="attendance-end" value="${escapeHtml(filters.end_date || '')}" /></label>${employeeFilter}<button class="button button-light" data-action="filter-attendance">Apply filters</button></div>`;
	view.innerHTML = `${heading('DAILY TIMEKEEPING', 'Attendance', 'Review attendance by employee and date range.', action)}${panel('Attendance summary', `Summary for ${dateText(filters.start_date)} – ${dateText(filters.end_date)}`, `<div class="panel-body muted">${summaryLine}　·　Total: <strong>${summary.total}</strong></div>`)}${panel('Attendance records', 'Filter records by a date range and employee', `${toolbar}<div class="table-wrap"><table><thead><tr><th>Employee</th><th>Date</th><th>Status</th><th>Notes</th></tr></thead><tbody>${rows || '<tr><td colspan="4" class="empty-state">No attendance records for this date range.</td></tr>'}</tbody></table></div>`)}`;
}

async function renderLeaves() {
	const result = await api('/leave-requests?page_size=100');
	const employeeMode = state.user.role !== 'admin';
	const rows = result.items.map((item) => `<tr><td>${employeeMode ? escapeHtml(item.employee_name) : formatPerson(item.employee_name, `Employee #${item.employee_id}`)}</td><td>${dateText(item.start_date)} – ${dateText(item.end_date)}</td><td>${escapeHtml(item.reason)}</td><td>${statusBadge(item.status)}</td><td>${item.reviewer_email ? escapeHtml(item.reviewer_email) : '—'}</td><td>${item.status === 'pending' && !employeeMode ? `<div class="table-actions"><button class="button button-primary button-small" data-action="review-leave" data-status="approved" data-id="${item.id}">Approve</button><button class="button button-danger button-small" data-action="review-leave" data-status="rejected" data-id="${item.id}">Reject</button></div>` : escapeHtml(item.reviewer_comment || '—')}</td></tr>`).join('');
	const action = employeeMode ? '<button class="button button-primary" data-action="new-leave">＋ Request leave</button>' : '';
	view.innerHTML = `${heading(employeeMode ? 'TIME AWAY' : 'TEAM REQUESTS', employeeMode ? 'My leave requests' : 'Leave requests', employeeMode ? 'Submit a request and check its review status.' : 'Review requests submitted by your employees.', action)}${panel('Leave request history', employeeMode ? 'Only your own leave records are shown' : 'Pending requests need an administrator decision', `<div class="table-wrap"><table><thead><tr><th>Employee</th><th>Dates</th><th>Reason</th><th>Status</th><th>Reviewed by</th><th>Review / comment</th></tr></thead><tbody>${rows || `<tr><td colspan="6" class="empty-state">${employeeMode ? 'No leave requests yet.' : 'No leave requests have been submitted.'}</td></tr>`}</tbody></table></div>`)}`;
}

async function renderProfile() {
	const employee = await api('/employees/me');
	const rows = `<tr><th>Employee ID</th><td>${escapeHtml(employee.employee_code)}</td></tr><tr><th>Work email</th><td>${escapeHtml(employee.email)}</td></tr><tr><th>Phone</th><td>${escapeHtml(employee.phone || '—')}</td></tr><tr><th>Department</th><td>${escapeHtml(employee.department_name)}</td></tr><tr><th>Designation</th><td>${escapeHtml(employee.designation)}</td></tr><tr><th>Joining date</th><td>${dateText(employee.joining_date)}</td></tr><tr><th>Employment status</th><td>${statusBadge(employee.employment_status)}</td></tr>`;
	const [attendance, leaves] = await Promise.all([api('/attendance?page_size=5'), api('/leave-requests?page_size=5')]);
	const personalAttendance = attendance.items.map((item) => `<tr><td>${dateText(item.attendance_date)}</td><td>${statusBadge(item.status)}</td></tr>`).join('');
	const personalLeaves = leaves.items.map((item) => `<tr><td>${dateText(item.start_date)} – ${dateText(item.end_date)}</td><td>${statusBadge(item.status)}</td></tr>`).join('');
	view.innerHTML = `${heading('YOUR ACCOUNT', 'My profile', 'Your personal information and recent work records.')}<div class="profile-grid">${panel('Employee details', '', `<div class="table-wrap"><table><tbody>${rows}</tbody></table></div>`)}${panel('Recent attendance', 'Your last five attendance records', `<div class="table-wrap"><table><tbody>${personalAttendance || '<tr><td class="empty-state">No attendance records yet.</td></tr>'}</tbody></table></div>`)}${panel('My leave requests', 'Your last five requests', `<div class="table-wrap"><table><tbody>${personalLeaves || '<tr><td class="empty-state">No leave requests yet.</td></tr>'}</tbody></table></div>`)}</div>`;
}

function readForm(form) {
	const data = Object.fromEntries(new FormData(form).entries());
	for (const key of ['department_id', 'employee_id']) if (key in data) data[key] = Number(data[key]);
	if ('salary' in data) data.salary = String(data.salary);
	for (const key of Object.keys(data)) if (data[key] === '') data[key] = null;
	return data;
}

document.addEventListener('click', async (event) => {
	const pageButton = event.target.closest('[data-page]');
	if (pageButton) {
		state.page = pageButton.dataset.page;
		document.querySelector('.sidebar').classList.remove('open');
		await renderPage();
		return;
	}
	const button = event.target.closest('[data-action]');
	if (!button) return;
	try {
		const id = Number(button.dataset.id);
		switch (button.dataset.action) {
			case 'refresh': await renderPage(); break;
			case 'filter-employees':
				await renderEmployees({ page: 1, search: document.querySelector('#employee-search').value.trim(), department_id: document.querySelector('#department-filter').value, employment_status: document.querySelector('#status-filter').value }); break;
			case 'employee-page': await renderEmployees({ ...state.employeeFilters, page: Number(button.dataset.pageNumber) }); break;
			case 'filter-attendance': {
				const start_date = document.querySelector('#attendance-start').value;
				const end_date = document.querySelector('#attendance-end').value;
				if (start_date && end_date && start_date > end_date) return toast('The start date must be on or before the end date.', true);
				await renderAttendanceFilter({ start_date, end_date, employee_id: document.querySelector('#attendance-employee')?.value || '' });
				break;
			}
			case 'add-employee': {
				const departments = (await api('/departments?page_size=100')).items;
				if (!departments.length) return toast('Create a department before adding employees.', true);
				openEditor('Add an employee', employeeFields(departments), { joining_date: today(), employment_status: 'active' }, 'Create employee'); break;
			}
			case 'edit-employee': {
				const [employee, departments] = await Promise.all([api(`/employees/${id}`), api('/departments?page_size=100')]);
				state.editor.employeeId = id;
				openEditor('Edit employee', employeeFields(departments.items, employee), employee, 'Save employee'); break;
			}
			case 'delete-employee':
				if (window.confirm('Delete this employee profile and its linked account and records? This cannot be undone.')) { await api(`/employees/${id}`, { method: 'DELETE' }); toast('Employee and linked account deleted.'); await renderEmployees(); } break;
			case 'add-department':
				state.editor.departmentId = null;
				openEditor('Add a department', [{ name: 'name', label: 'Department name', required: true, maxlength: 120 }, { name: 'description', label: 'Description', type: 'textarea', full: true, maxlength: 500 }], {}); break;
			case 'edit-department': {
				const department = (await api('/departments?page_size=100')).items.find((item) => item.id === id);
				state.editor.departmentId = id;
				openEditor('Edit department', [{ name: 'name', label: 'Department name', required: true, maxlength: 120 }, { name: 'description', label: 'Description', type: 'textarea', full: true, maxlength: 500 }], department); break;
			}
			case 'delete-department':
				if (window.confirm('Delete this department? Departments with employees cannot be deleted.')) { await api(`/departments/${id}`, { method: 'DELETE' }); toast('Department deleted.'); await renderDepartments(); } break;
			case 'record-attendance': {
				const employees = state.attendanceEmployees || (await api('/employees?page_size=100')).items;
				if (!employees.length) return toast('Add an employee before recording attendance.', true);
				openEditor('Record attendance', [{ name: 'employee_id', label: 'Employee', type: 'select', required: true, options: employees.map((item) => ({ value: item.id, label: `${item.name} · ${item.employee_code}` })) }, { name: 'attendance_date', label: 'Date', type: 'date', required: true }, { name: 'status', label: 'Status', type: 'select', required: true, options: ['present', 'absent', 'late', 'half_day'].map((value) => ({ value, label: titleCase(value) })) }, { name: 'notes', label: 'Notes', type: 'textarea', full: true }], { attendance_date: today(), status: 'present' }, 'Record attendance'); break;
			}
			case 'new-leave':
				openEditor('Request time off', [{ name: 'start_date', label: 'First day', type: 'date', required: true }, { name: 'end_date', label: 'Last day', type: 'date', required: true }, { name: 'reason', label: 'Reason for leave', type: 'textarea', required: true, full: true }], { start_date: today(), end_date: today() }, 'Submit request'); break;
			case 'review-leave': {
				let reviewer_comment = window.prompt(`${titleCase(button.dataset.status)} this request. Optional comment:`);
				if (reviewer_comment === null) break;
				await api(`/leave-requests/${id}`, { method: 'PATCH', body: { status: button.dataset.status, reviewer_comment: reviewer_comment || null } });
				toast(`Leave request ${button.dataset.status}.`); await renderLeaves(); break;
			}
		}
	} catch (error) { toast(error.message, true); }
});

document.querySelector('#cancel-editor').addEventListener('click', () => editor.close());
editorForm.addEventListener('submit', async (event) => {
	event.preventDefault();
	if (!state.editor) return;
	const action = state.editor;
	const payload = readForm(editorForm);
	document.querySelector('#save-editor').disabled = true;
	try {
		if (state.page === 'employees') {
			if (action.employeeId) await api(`/employees/${action.employeeId}`, { method: 'PATCH', body: payload });
			else await api('/employees', { method: 'POST', body: payload });
			toast(action.employeeId ? 'Employee profile updated.' : 'Employee added.');
		} else if (state.page === 'departments') {
			if (action.departmentId) await api(`/departments/${action.departmentId}`, { method: 'PATCH', body: payload });
			else await api('/departments', { method: 'POST', body: payload });
			toast(action.departmentId ? 'Department updated.' : 'Department added.');
		} else if (state.page === 'attendance') {
			await api('/attendance', { method: 'POST', body: payload });
			toast('Attendance recorded.');
		} else if (state.page === 'leaves') {
			await api('/leave-requests', { method: 'POST', body: payload });
			toast('Leave request submitted.');
		}
		editor.close();
		state.editor = null;
		await renderPage();
	} catch (error) { toast(error.message, true); }
	finally { document.querySelector('#save-editor').disabled = false; }
});

document.querySelector('#logout').addEventListener('click', async () => {
	try { await api('/auth/logout', { method: 'POST' }); } finally { window.location.assign('/login'); }
});
document.querySelector('#menu-toggle').addEventListener('click', () => document.querySelector('.sidebar').classList.toggle('open'));
start();
