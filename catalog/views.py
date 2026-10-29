from django.shortcuts import render
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import permission_required, login_required
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from .forms import RenewBookForm
from .models import Author
from datetime import date, timedelta

# Create your views here.
from .models import Book, Author, BookInstance, Genre

def index(request):
    """View function for home page of site."""

    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()

    num_instances_available = BookInstance.objects.filter(status__exact='a').count()

    num_authors = Author.objects.count()
    num_genres = Genre.objects.filter(name__icontains='fiction').count()
    num_books_with_the = Book.objects.filter(title__icontains='the').count()

    num_visits = request.session.get('num_visits', 0)
    num_visits += 1
    request.session['num_visits'] = num_visits

    context = {
        'num_books': num_books,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
        'num_genres': num_genres,
        'num_books_with_the': num_books_with_the,
        'num_visits': num_visits,
    }

    return render(request, 'index.html', context=context)

class BookListView(generic.ListView):
    model = Book
    paginate_by = 10

class BookDetailView(generic.DetailView):
    model = Book

class AuthorListView(generic.ListView):
    model = Author
    paginate_by = 10

class AuthorDetailView(generic.DetailView):
    model = Author

class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
    """Display books currently borrowed by the logged-in user."""

    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_user.html'
    context_object_name = 'bookinstance_list'
    paginate_by = 10

    def get_queryset(self):
        return (
            BookInstance.objects
            .filter(borrower=self.request.user, status__exact='o')
            .order_by('due_back')
        )

class LoanedBooksAllListView(PermissionRequiredMixin, generic.ListView):
    """Display all borrowed books for librarians."""

    model = BookInstance
    permission_required = 'catalog.can_mark_returned'
    template_name = 'catalog/bookinstance_list_borrowed_all.html'
    context_object_name = 'bookinstance_list'
    paginate_by = 10

    def get_queryset(self):
        return (
            BookInstance.objects
            .filter(status__exact='o')
            .order_by('due_back')
        )

@login_required
@permission_required("catalog.can_mark_returned", raise_exception=True)
def renew_book_librarian(request, pk):
    book_instance = get_object_or_404(BookInstance, pk=pk)

    if request.method == "POST":
        form = RenewBookForm(request.POST)

        if form.is_valid():
            book_instance.due_back = form.cleaned_data["renewal_date"]
            book_instance.save()

            return HttpResponseRedirect(reverse("all-borrowed"))

    else:
        proposed_renewal_date = date.today() + timedelta(weeks=3)
        form = RenewBookForm(
            initial={"renewal_date": proposed_renewal_date}
        )

    context = {
        "form": form,
        "book_instance": book_instance,
    }

    return render(
        request,
        "catalog/book_renew_librarian.html",
        context,
    )

class AuthorCreate(PermissionRequiredMixin, generic.CreateView):
    model = Author
    fields = ["first_name", "last_name", "date_of_birth", "date_of_death"]
    permission_required = "catalog.add_author"


class AuthorUpdate(PermissionRequiredMixin, generic.UpdateView):
    model = Author
    fields = ["first_name", "last_name", "date_of_birth", "date_of_death"]
    permission_required = "catalog.change_author"


class AuthorDelete(PermissionRequiredMixin, generic.DeleteView):
    model = Author
    success_url = reverse_lazy("authors")
    permission_required = "catalog.delete_author"

class BookCreate(PermissionRequiredMixin, generic.CreateView):
    model = Book
    fields = ["title", "summary", "isbn", "genre", "language"]
    permission_required = "catalog.add_book"


class BookUpdate(PermissionRequiredMixin, generic.UpdateView):
    model = Book
    fields = ["title", "summary", "isbn", "genre", "language"]
    permission_required = "catalog.change_book"


class BookDelete(PermissionRequiredMixin, generic.DeleteView):
    model = Book
    success_url = reverse_lazy("books")
    permission_required = "catalog.delete_book"
