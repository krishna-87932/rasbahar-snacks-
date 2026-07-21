from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=10, blank=True, help_text='Emoji icon')
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class MenuItem(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to='menu_items/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_veg = models.BooleanField(default=True)
    is_spicy = models.BooleanField(default=False)
    calories = models.PositiveIntegerField(null=True, blank=True)
    prep_time_minutes = models.PositiveIntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} (₹{self.price})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class AddOn(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to='addons/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    is_veg = models.BooleanField(default=True)
    menu_items = models.ManyToManyField(MenuItem, related_name='addons', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} (₹{self.price})"


class DailyMenu(models.Model):
    """A time-bound daily menu (e.g., Lunch Thali 10 AM–1 PM)."""
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    icon = models.CharField(max_length=10, blank=True, default='🍱', help_text='Emoji icon')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_time']
        verbose_name_plural = 'Daily Menus'

    def __str__(self):
        return f"{self.title} ({self.start_time.strftime('%I:%M %p')} – {self.end_time.strftime('%I:%M %p')})"

    def is_currently_active(self):
        """Check if current time falls within start_time and end_time."""
        from django.utils import timezone
        now = timezone.localtime().time()
        if self.start_time <= self.end_time:
            return self.is_active and self.start_time <= now <= self.end_time
        else:
            # Handles overnight menus (e.g., 10 PM – 2 AM)
            return self.is_active and (now >= self.start_time or now <= self.end_time)


class DailyMenuItem(models.Model):
    """An item in a daily menu with quantity tracking."""
    daily_menu = models.ForeignKey(DailyMenu, on_delete=models.CASCADE, related_name='daily_items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='daily_menu_entries')
    quantity_total = models.PositiveIntegerField(default=0, help_text='Total quantity available for the day')
    quantity_sold = models.PositiveIntegerField(default=0, help_text='Quantity sold so far today')
    date = models.DateField(help_text='Date for which this quantity applies')

    class Meta:
        ordering = ['daily_menu', 'menu_item']
        unique_together = ('daily_menu', 'menu_item', 'date')

    def __str__(self):
        return f"{self.menu_item.name} × {self.quantity_total} ({self.date})"

    @property
    def quantity_remaining(self):
        return max(0, self.quantity_total - self.quantity_sold)

    @property
    def is_sold_out(self):
        return self.quantity_remaining <= 0
