import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'

import MainLayout from './components/layout/MainLayout'
import StudentPortalAccess from './components/layout/StudentPortalAccess'
import ProtectedRoute from './components/ProtectedRoute'
import LoadingLine from './components/ui/LoadingLine'
import InterviewsListPage from './pages/interviews/InterviewsListPage'
import InternsListPage from './pages/interns/InternsListPage'
import LoginPage from './pages/LoginPage'
import NoAccessPage from './pages/NoAccessPage'
import NotFoundPage from './pages/NotFoundPage'

const InterviewFormPage = lazy(() => import('./pages/interviews/InterviewFormPage'))
const InternFormPage = lazy(() => import('./pages/interns/InternFormPage'))
const ManagerDetailPage = lazy(() => import('./pages/employees/ManagerDetailPage'))
const AdminKpiPage = lazy(() => import('./pages/employees/AdminKpiPage'))
const AdminDevelopersPage = lazy(() => import('./pages/employees/AdminDevelopersPage'))
const DebtFormPage = lazy(() => import('./pages/debts/DebtFormPage'))
const DebtsByMonthPage = lazy(() => import('./pages/debts/DebtsByMonthPage'))
const OfferFormPage = lazy(() => import('./pages/offers/OfferFormPage'))
const ManagersListPage = lazy(() => import('./pages/managers/ManagersListPage'))
const SadInternListPage = lazy(() => import('./pages/sadIntern/SadInternListPage'))
const SadInternFormPage = lazy(() => import('./pages/sadIntern/SadInternFormPage'))
const DevelopersListPage = lazy(() => import('./pages/developers/DevelopersListPage'))
const DirectionsListPage = lazy(() => import('./pages/directions/DirectionsListPage'))
const DirectionFormPage = lazy(() => import('./pages/directions/DirectionFormPage'))
const CompaniesListPage = lazy(() => import('./pages/companies/CompaniesListPage'))
const CompanyFormPage = lazy(() => import('./pages/companies/CompanyFormPage'))
const CompanyMergePage = lazy(() => import('./pages/companies/CompanyMergePage'))
const KnowledgeBaseArticleFormPage = lazy(() => import('./pages/knowledgeBase/KnowledgeBaseArticleFormPage'))
const InterviewsDatabaseListPage = lazy(() => import('./pages/interviewsDatabase/InterviewsDatabaseListPage'))
const InternsPortalPage = lazy(() => import('./pages/internsPortal/InternsPortalPage'))

import EmployeesListPage from './pages/employees/EmployeesListPage'
import KnowledgeBaseArticlePage from './pages/knowledgeBase/KnowledgeBaseArticlePage'
import KnowledgeBaseHomePage from './pages/knowledgeBase/KnowledgeBaseHomePage'
import DebtsListPage from './pages/debts/DebtsListPage'
import HelpPage from './pages/help/HelpPage'
import OffersListPage from './pages/offers/OffersListPage'

/**
 * Маршруты приложения. Форма собеседования — отдельный чанк (React.lazy).
 */
function AppRoutes() {
  return (
    <Suspense fallback={<LoadingLine message="Загрузка страницы…" />}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/no-access" element={<NoAccessPage />} />

        <Route
          element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }
        >
          <Route element={<StudentPortalAccess />}>
          <Route path="/" element={<Navigate to="/interviews" replace />} />
          <Route path="interviews" element={<InterviewsListPage />} />
          <Route path="interviews/new" element={<InterviewFormPage />} />
          <Route path="interviews/:id/duplicate" element={<InterviewFormPage />} />
          <Route path="interviews/:id/edit" element={<InterviewFormPage />} />
          <Route path="interviews-database" element={<InterviewsDatabaseListPage />} />
          <Route path="interns" element={<InternsListPage />} />
          <Route path="interns/new" element={<InternFormPage />} />
          <Route path="interns/:id/edit" element={<InternFormPage />} />
          <Route path="knowledge-base" element={<KnowledgeBaseHomePage />} />
          <Route path="knowledge-base/:sectionId/article/new" element={<KnowledgeBaseArticleFormPage mode="create" />} />
          <Route
            path="knowledge-base/:sectionId/article/:filename/edit"
            element={<KnowledgeBaseArticleFormPage mode="edit" />}
          />
          <Route path="knowledge-base/:sectionId/article/:filename" element={<KnowledgeBaseArticlePage />} />
          <Route path="debts" element={<DebtsListPage />} />
          <Route path="debts/new" element={<DebtFormPage />} />
          <Route path="debts/:id/edit" element={<DebtFormPage />} />
          <Route path="debts/by-month" element={<DebtsByMonthPage />} />
          <Route path="offers" element={<OffersListPage />} />
          <Route path="offers/new" element={<OfferFormPage />} />
          <Route path="offers/:id/edit" element={<OfferFormPage />} />
          <Route path="employees/admin/kpi" element={<AdminKpiPage />} />
          <Route path="employees/admin/developers" element={<AdminDevelopersPage />} />
          <Route path="employees/:managerEmail" element={<ManagerDetailPage />} />
          <Route path="employees" element={<EmployeesListPage />} />
          <Route path="companies" element={<CompaniesListPage />} />
          <Route path="companies/new" element={<Navigate to="/companies" replace />} />
          <Route path="companies/merge" element={<CompanyMergePage />} />
          <Route path="companies/:id/edit" element={<CompanyFormPage />} />
          <Route path="managers" element={<ManagersListPage />} />
          <Route path="directions" element={<DirectionsListPage />} />
          <Route path="directions/new" element={<DirectionFormPage />} />
          <Route path="sad-intern" element={<SadInternListPage />} />
          <Route path="sad-intern/new" element={<SadInternFormPage />} />
          <Route path="sad-intern/:id/edit" element={<SadInternFormPage />} />
          <Route path="developers" element={<DevelopersListPage />} />
          <Route
            path="help"
            element={
              <ProtectedRoute roles={['admin']}>
                <HelpPage />
              </ProtectedRoute>
            }
          />
          <Route path="interns-portal" element={<InternsPortalPage />} />
          <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Route>
      </Routes>
    </Suspense>
  )
}

export default AppRoutes
