
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Sum, F
from random import choices
from .models import Quote, Source
from .forms import QuoteForm, SourceForm
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Sum, Avg, F
from random import choices
from .models import Quote, Source
from .forms import QuoteForm, SourceForm

def popular_quotes(request):
    print("=== DEBUG: popular_quotes view called ===")
    
    # Получаем параметры фильтрации
    source_type = request.GET.get('type', 'all')
    sort_by = request.GET.get('sort', 'likes')
    
    # Базовый queryset
    quotes = Quote.objects.all()
    print(f"DEBUG: Initial quotes count: {quotes.count()}")
    
    # Фильтрация по типу источника
    if source_type != 'all':
        quotes = quotes.filter(source__type=source_type)
        print(f"DEBUG: After filtering by {source_type}: {quotes.count()}")
    
    # Сортировка
    if sort_by == 'views':
        quotes = quotes.order_by('-views_count')[:10]
    elif sort_by == 'ratio':
        quotes = quotes.annotate(
            total_reactions=F('likes') + F('dislikes')
        ).filter(total_reactions__gt=0).annotate(
            like_ratio=100.0 * F('likes') / F('total_reactions')
        ).order_by('-like_ratio')[:10]
    else:
        quotes = quotes.order_by('-likes')[:10]
    
    print(f"DEBUG: Final quotes count: {quotes.count()}")
    
    # Вычисляем like_ratio для каждой цитаты
    for quote in quotes:
        total_reactions = quote.likes + quote.dislikes
        quote.like_ratio = (quote.likes / total_reactions * 100) if total_reactions > 0 else 0
    
    # Статистика для дашборда
    total_quotes = Quote.objects.count()
    total_sources = Source.objects.count()
    total_likes = Quote.objects.aggregate(total=Sum('likes'))['total'] or 0
    total_views = Quote.objects.aggregate(total=Sum('views_count'))['total'] or 0
    avg_likes = Quote.objects.aggregate(avg=Avg('likes'))['avg'] or 0
    
    print(f"DEBUG: Stats - quotes: {total_quotes}, sources: {total_sources}, likes: {total_likes}")
    
    # Расчет вовлеченности
    total_dislikes = Quote.objects.aggregate(total=Sum('dislikes'))['total'] or 0
    total_reactions = total_likes + total_dislikes
    engagement_rate = (total_reactions / total_views * 100) if total_views > 0 else 0
    
    # Топ-5 цитат для графика
    top_5_quotes = list(Quote.objects.order_by('-likes')[:5])
    max_likes = top_5_quotes[0].likes if top_5_quotes else 1
    
    print(f"DEBUG: Top 5 quotes count: {len(top_5_quotes)}")
    
    for quote in top_5_quotes:
        quote.bar_height = (quote.likes / max_likes) * 150
    
    context = {
        'quotes': quotes,
        'total_quotes': total_quotes,
        'total_sources': total_sources,
        'total_likes': total_likes,
        'total_views': total_views,
        'avg_likes': avg_likes,
        'engagement_rate': engagement_rate,
        'top_5_quotes': top_5_quotes,
    }
    
    print("DEBUG: Context prepared, rendering template...")
    return render(request, 'quotes/popular_quotes.html', context)
def random_quote(request):
    # Получаем все цитаты с их весами
    quotes = Quote.objects.all()
    weights = [quote.weight for quote in quotes]
    
    # Выбираем случайную цитату с учетом весов
    if quotes:
        selected_quote = choices(quotes, weights=weights, k=1)[0]
        selected_quote.views_count += 1
        selected_quote.save()
    else:
        selected_quote = None
    
    return render(request, 'quotes/random_quote.html', {
        'quote': selected_quote,
        'total_views': Quote.objects.aggregate(total=Sum('views_count'))['total'] or 0
    })
def add_quote(request):
    if request.method == 'POST':
        form = QuoteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('random_quote')
    else:
        form = QuoteForm()
    
    return render(request, 'quotes/add_quote.html', {'form': form})

def add_source(request):
    if request.method == 'POST':
        form = SourceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('add_quote')
    else:
        form = SourceForm()
    
    return render(request, 'quotes/add_source.html', {'form': form})

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def like_quote(request, quote_id):
    quote = get_object_or_404(Quote, id=quote_id)
    ip_address = get_client_ip(request)
    
    if quote.has_user_voted(ip_address):
        return JsonResponse({
            'success': False, 
            'message': 'Вы уже голосовали за эту цитату',
            'likes': quote.likes, 
            'dislikes': quote.dislikes
        })
    
    success = quote.add_vote(ip_address, 'like')
    return JsonResponse({
        'success': success,
        'likes': quote.likes, 
        'dislikes': quote.dislikes
    })

def dislike_quote(request, quote_id):
    quote = get_object_or_404(Quote, id=quote_id)
    ip_address = get_client_ip(request)
    
    if quote.has_user_voted(ip_address):
        return JsonResponse({
            'success': False, 
            'message': 'Вы уже голосовали за эту цитату',
            'likes': quote.likes, 
            'dislikes': quote.dislikes
        })
    
    success = quote.add_vote(ip_address, 'dislike')
    return JsonResponse({
        'success': success,
        'likes': quote.likes, 
        'dislikes': quote.dislikes
    })
