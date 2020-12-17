from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.db.models.functions import Lower
from .forms import ReviewForm, ProductForm

from .models import Product, Category, Review

# Create your views here.


def all_products(request):
    """ A view to show all products, including sorting and search queries """

    products = Product.objects.all()
    query = None
    categories = None
    sort = None
    direction = None

    if request.GET:
        if 'sort' in request.GET:
            sortkey = request.GET['sort']
            sort = sortkey
            if sortkey == 'name':
                sortkey = 'lower_name'
                products = products.annotate(lower_name=Lower('name'))

            if 'direction' in request.GET:
                direction = request.GET['direction']
                if direction == 'desc':
                    sortkey = f'-{sortkey}'
            products = products.order_by(sortkey)


    if request.GET:
        if 'category' in request.GET:
            categories = request.GET['category'].split(',')
            products = products.filter(category__name__in=categories)
            categories = Category.objects.filter(name__in=categories)

        if 'q' in request.GET:
            query = request.GET['q']
            if not query:
                messages.error(request, "You didn't enter any search criteria!")
                return redirect(reverse('products'))
 
            queries = ( Q(name__icontains=query) | Q(name_ro__icontains=query) |
            Q(name_ru__icontains=query) | Q(description__icontains=query) |
            Q(description_ro__icontains=query) | Q(description_ru__icontains=query))
            products = products.filter(queries)

    current_sorting = f'{sort}_{direction}'

    context = {
        'products': products,
        'search_term': query,
        'current_categories': categories,
        'current_sorting': current_sorting,
    }

    return render(request, 'products/products.html', context)


def product_detail(request, product_id):
    """ A view to show individual product details """

    product = get_object_or_404(Product, pk=product_id)
    reviews = Review.objects.filter(product=product_id)

    context = {
        'product': product,
        'reviews': reviews,
    }

    return render(request, 'products/product_detail.html', context)


def add_product(request):
    """ Add a product to the store """
    form = ProductForm()
    template = 'products/add_product.html'
    context = {
        'form': form,
    }

    return render(request, template, context)


def add_review(request, product_id):
    """ A view to add review to a product"""

    product = Product.objects.get(pk=product_id)

    if request.method == "POST":
        form = ReviewForm(request.POST or None)
        if form.is_valid():
            data = form.save(commit=False)
            data.comment = request.POST["comment"]
            data.user = request.user
            data.product = product
            data.save()
            messages.success(request, 'Review submitted!')
            return redirect('product_detail', product_id)
        else:
            messages.error(request, 'Failed to submit review. Please ensure the form is valid.')
    else:
        form = ReviewForm()
        template = 'products/product_detail.html'
    return render(request, template, {"form": form})


def edit_review(request, product_id, review_id):
        """A view to edit product reviews"""

        product = get_object_or_404(Product, pk=product_id)
        review = get_object_or_404(Review, product=product, pk=review_id)

        if request.user == review.user:
            if request.method == "POST":
                form = ReviewForm(request.POST, instance=review)
                if form.is_valid():
                    data = form.save(commit=False)
                    data.save()
                    messages.success(request, 'Review updated!')
                    return redirect('product_detail', product_id)
                else:
                    messages.error(request, 'Failed to update review. Please ensure the form is valid.')
                    return redirect('product_detail', product_id)
            else:
                form = ReviewForm(instance=review)
                return render(request, 'products/editreview.html', {"form": form})
        else:
            return redirect('product_detail', product_id)


def delete_review(request, product_id, review_id):
        """A view to delete product review"""

        product = get_object_or_404(Product, pk=product_id)
        review = get_object_or_404(Review, product=product, pk=review_id)

        if request.user == review.user:
            review.delete()
            messages.success(request, 'Review delete successfully')

        return redirect('product_detail', product_id)
