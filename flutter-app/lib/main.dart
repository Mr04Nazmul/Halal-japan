import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() => runApp(const HalalApp());

class HalalApp extends StatefulWidget {
  const HalalApp({super.key});
  @override
  State<HalalApp> createState() => _HalalAppState();
}

class _HalalAppState extends State<HalalApp> {
  String language = 'en';
  @override
  void initState() {
    super.initState();
    SharedPreferences.getInstance().then((prefs) {
      if (mounted) setState(() => language = prefs.getString('language') ?? 'en');
    });
  }

  void setLanguage(String value) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('language', value);
    if (mounted) setState(() => language = value);
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Japan Halal Checker',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xff22c7a2), brightness: Brightness.dark),
        useMaterial3: true,
        scaffoldBackgroundColor: const Color(0xff07121b),
      ),
      home: HomePage(language: language, onLanguage: setLanguage),
    );
  }
}

const labels = <String, Map<String, String>>{
  'en': {'search':'Search a Japanese product','scan':'Scan barcode','lookup':'Search','settings':'Settings','about':'Created by Hossain Najmul','unknown':'Not verified','notice':'Product listing is not religious certification. Verify uncertain ingredients with the manufacturer or a trusted halal certifier.','hint':'Barcode or product name','missing':'No product found','ingredients':'Ingredients','source':'Source'},
  'bn': {'search':'জাপানের পণ্য খুঁজুন','scan':'বারকোড স্ক্যান','lookup':'সার্চ','settings':'সেটিংস','about':'তৈরি করেছেন Hossain Najmul','unknown':'যাচাই হয়নি','notice':'পণ্যের তথ্য ধর্মীয় সার্টিফিকেশন নয়। অনিশ্চিত উপাদানের উৎস প্রস্তুতকারক বা বিশ্বস্ত হালাল সার্টিফায়ারের কাছে যাচাই করুন।','hint':'বারকোড বা পণ্যের নাম','missing':'পণ্য পাওয়া যায়নি','ingredients':'উপাদান','source':'তথ্যের উৎস'},
  'ja': {'search':'日本の商品を検索','scan':'バーコードをスキャン','lookup':'検索','settings':'設定','about':'製作者 Hossain Najmul','unknown':'未確認','notice':'商品情報はハラール認証ではありません。不明な原材料は製造元または認証機関に確認してください。','hint':'バーコードまたは商品名','missing':'商品が見つかりません','ingredients':'原材料','source':'情報源'},
};

class HomePage extends StatefulWidget {
  final String language;
  final ValueChanged<String> onLanguage;
  const HomePage({super.key, required this.language, required this.onLanguage});
  @override
  State<HomePage> createState() => _HomePageState();
}

class Product {
  final String name, brand, barcode, ingredients, image, source;
  Product({required this.name, required this.brand, required this.barcode, required this.ingredients, required this.image, required this.source});
  factory Product.fromOff(Map<String, dynamic> item) => Product(
    name: (item['product_name'] ?? item['product_name_en'] ?? '').toString(),
    brand: (item['brands'] ?? '').toString(),
    barcode: (item['code'] ?? '').toString(),
    ingredients: (item['ingredients_text'] ?? item['ingredients_text_ja'] ?? '').toString(),
    image: (item['image_front_url'] ?? item['image_url'] ?? '').toString(),
    source: 'Open Food Facts (community-contributed)',
  );
}

class _HomePageState extends State<HomePage> {
  final input = TextEditingController();
  bool busy = false;
  String? error;
  List<Product> results = [];

  String get lang => labels.containsKey(widget.language) ? widget.language : 'en';
  String tr(String key) => labels[lang]![key] ?? labels['en']![key] ?? key;
  @override
  void dispose() { input.dispose(); super.dispose(); }

  Future<void> search([String? query]) async {
    final q = (query ?? input.text).trim();
    if (q.isEmpty || busy) return;
    setState(() { busy = true; error = null; results = []; });
    try {
      final barcode = RegExp(r'^\d{8,14}$').hasMatch(q);
      final url = barcode
        ? Uri.https('world.openfoodfacts.org', '/api/v2/product/$q.json')
        : Uri.https('world.openfoodfacts.org', '/cgi/search.pl', {'search_terms':q,'search_simple':'1','action':'process','json':'1','page_size':'25'});
      final response = await http.get(url, headers: {'User-Agent':'JapanHalalChecker/0.1 (OpenFoodFacts client)'})
          .timeout(const Duration(seconds: 15));
      if (response.statusCode != 200) throw Exception('HTTP ${response.statusCode}');
      final payload = jsonDecode(response.body) as Map<String, dynamic>;
      final items = barcode
          ? (payload['product'] is Map ? [payload['product']] : <dynamic>[])
          : (payload['products'] as List? ?? <dynamic>[]);
      final products = items.whereType<Map<String, dynamic>>().map(Product.fromOff).where((p) => p.name.isNotEmpty).toList();
      if (!mounted) return;
      setState(() { results = products; if (products.isEmpty) error = tr('missing'); });
    } catch (e) {
      if (mounted) setState(() => error = 'Lookup failed: $e');
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> scan() async {
    final code = await Navigator.push<String>(context, MaterialPageRoute(builder: (_) => const ScannerPage()));
    if (code != null) { input.text = code; await search(code); }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Japan Halal Checker'), actions: [
        PopupMenuButton<String>(
          onSelected: (value) => widget.onLanguage(value),
          itemBuilder: (_) => const [
            PopupMenuItem(value:'en',child:Text('English')),
            PopupMenuItem(value:'bn',child:Text('বাংলা')),
            PopupMenuItem(value:'ja',child:Text('日本語')),
          ],
          icon: const Icon(Icons.language),
        ),
      ]),
      body: ListView(padding: const EdgeInsets.all(18), children: [
        Text(tr('search'), style: Theme.of(context).textTheme.headlineSmall),
        const SizedBox(height: 14),
        TextField(controller: input, onSubmitted: search, decoration: InputDecoration(
          hintText: tr('hint'), border: const OutlineInputBorder(),
          suffixIcon: IconButton(icon: const Icon(Icons.search), onPressed: () => search()),
        )),
        const SizedBox(height: 12),
        Row(children: [
          Expanded(child: FilledButton.icon(onPressed: scan, icon: const Icon(Icons.qr_code_scanner), label: Text(tr('scan')))),
          const SizedBox(width: 8),
          FilledButton.tonal(onPressed: busy ? null : () => search(), child: Text(tr('lookup'))),
        ]),
        const SizedBox(height: 16),
        if (busy) const LinearProgressIndicator(),
        if (error != null) Padding(padding: const EdgeInsets.all(12),child: Text(error!)),
        for (final p in results) ProductCard(product: p, ingredientsLabel: tr('ingredients'), sourceLabel: tr('source'), statusLabel: tr('unknown')),
        const SizedBox(height: 20),
        Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.start,children: [
          const Text('Verification policy',style:TextStyle(fontWeight:FontWeight.bold)),
          const SizedBox(height: 8),
          Text(tr('notice')),
        ]))),
        const SizedBox(height: 20),
        Text(tr('about'),textAlign:TextAlign.center,style: const TextStyle(color:Colors.white54)),
      ]),
    );
  }
}

class ProductCard extends StatelessWidget {
  final Product product;
  final String ingredientsLabel, sourceLabel, statusLabel;
  const ProductCard({super.key,required this.product,required this.ingredientsLabel,required this.sourceLabel,required this.statusLabel});
  @override
  Widget build(BuildContext context) {
    final ingredients = product.ingredients.toLowerCase();
    final flagged = ['豚','pork','lard','ラード','酒精','アルコール','ethanol','gelatin','ゼラチン','mirin','みりん','酒'];
    final hits = flagged.where((term) => ingredients.contains(term)).toList();
    return Card(margin: const EdgeInsets.only(bottom: 12),child:Padding(padding: const EdgeInsets.all(14),child:Column(crossAxisAlignment: CrossAxisAlignment.start,children:[
      if (product.image.startsWith('https://')) Image.network(product.image,height:130,fit:BoxFit.contain,errorBuilder:(_,__,___)=>const SizedBox.shrink()),
      Text(product.name,style:Theme.of(context).textTheme.titleMedium),
      Text(product.brand),
      const SizedBox(height: 6),
      const Chip(label: Text('HALAL STATUS: NOT VERIFIED')),
      if (hits.isNotEmpty) Text('Check ingredient origins: ${hits.join(", ")}',style:const TextStyle(color:Colors.orangeAccent)),
      if (product.ingredients.isEmpty) const Text('Ingredient list unavailable — cannot assess.'),
      if (product.ingredients.isNotEmpty) Text('$ingredientsLabel: ${product.ingredients}'),
      const SizedBox(height: 8),
      Text('$sourceLabel: ${product.source}',style:const TextStyle(fontSize:12,color:Colors.white60)),
    ])));
  }
}

class ScannerPage extends StatefulWidget {
  const ScannerPage({super.key});
  @override
  State<ScannerPage> createState() => _ScannerPageState();
}
class _ScannerPageState extends State<ScannerPage> {
  bool captured = false;
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Barcode scanner')),
    body: MobileScanner(
      onDetect: (capture) {
        if (captured) return;
        for (final item in capture.barcodes) {
          final raw = item.rawValue;
          if (raw != null && RegExp(r'^\d{8,14}$').hasMatch(raw)) {
            captured = true;
            Navigator.pop(context, raw);
            break;
          }
        }
      },
    ),
  );
}
